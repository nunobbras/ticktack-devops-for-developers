
'''
[NBB] How to 

  ### Run Like this:
  ### fab [host_name] compile_type:[compile_type] branch_name:[branch] <instruction>
  
  ###instruction:
  deploy:

  ###########
  Examples:
  
  deploy usage:
  1st) fab git_push ou fab git_push:False (no build, just push)
  2nd) fab azure_prod compile_type:prod branch_name:dev deploy:tack swap_DNS:tack

  Other funcs:

  1) fab azure_prod rebuild_containers:tack (rebuilds from scratch all containers (not the servers))
  2) fab azure_prod restart_services:tack 
  3) fab azure_prod full_rebuild (rebuilds all the environment containers AND the servers)
  4) fab azure_prod compile_type:prod branch_name:TEST1 codebase_to_static:tack
  5) fab azure_prod swap_DNS:tack
  6) 

  fab azure_dev compile_type:prod branch_name:dev deploy:tack or deploy:tick swap_DNS:tack
  
  


  ##############
  [host_name] = [azure_dev, azure_prod, local_docker] - 
  this affects where to deploy - and what machines to deploy
  also, service_type that is, what type of services: email pass, DB (prod or dev) etc. (from .env files)
   see their definitions
  
  
  ##############
  [compile_type] = [prod, dev, shared_code...] - compilation type: 
  this affects compilation type prod and dev (static code and django), 
  and code deploy through shared directory (shared_code) or else, through git

  ##############
  [branch_name] = [prod, dev, other...] - what to deploy

  <instruction> - deploy:tick, deploy:tack, etc (see available with fab --list)

  don't forget to prepare your branch (commit, add and pull should be done!) 
  git merge develop --no-ff



#RULES
 
#There should be 1 .env file per host_name which defines their local configurations
#*static* is the folder where active code is - fabfile copy to there the code for deploy.

#service_type - defines type of services, e.g. DB, email, django app secret key, etc 
(info from .env_XXX, added in docker compose (yml) to the machine)
service type is what choose the kind of yml for docker compose. since full_[prod]_deploy.yml are the 
rules for [prod, dev, staging] type of service to install - 
this is changed with the service type.
'''

from sys import argv
from fabric.api import local, run
from fabric.state import env
from fabric.context_managers import settings, prefix, cd, lcd
from fabric.api import task
import time
import os 
import ipdb

import sys
from dynect.DynectDNS import DynectRest as _DynectRest


WORKING_DIR = os.environ.get('WORKING_DIR')
if WORKING_DIR == None:
  print "No WORKING_DIR created. Please create (source) your local .env file. Ask NBB for it."

############################
#host_name definition
def azure_dev():  
  env.service_name = "azure_dev"
  env.service_type = "dev"
  env.host_names = {'tick':'serverdevtick', 'tack':'serverdevtack'}
  env.hosts_url = {'tick':'serverdevtick.cloudapp.net', 'tack':'serverdevtack.cloudapp.net'}  
  #machine name is important: tick is the main one (1); tack (are) secondary; worker should be workers:
  #env.host_names = {'tick':'serverdevtick', 'tack':'serverdevtack', 'worker':'xpto'}  

def azure_prod():
  env.service_name = "azure_prod"
  env.service_type = "prod"
  env.host_names = {'tick':'serverprodtick', 'tack':'serverprodtack'}
  env.hosts_url = {'tick':'serverprodtick.cloudapp.net', 'tack':'serverprodtack.cloudapp.net'}  

def local_docker():
  env.service_name = "local_docker"
  env.service_type = "local_docker"
  env.host_names = {'tick':'docker-vm'}
  env.hosts_url = {'tick':'localhost'}    



############################
#define branch 
def branch_name(_branch):
  env.branch = _branch

############################
#define branch 
def compile_type(compile_type):
  _list = {'prod':'production', 'dev':'development'}
  env.compile_dir = _list[compile_type]
  env.compile_type = compile_type


prompt = '> '




def git_push(copyFiles=False):
  #Corre local django server automatd tests
  #local("../web/restapi/manage.py test restapi")
  print ("commit message:")
  commit_msg = raw_input(prompt)

  if copyFiles==False:
    print ("buildings...just prod NO IMAGES !")
    
    with lcd(WORKING_DIR + "/web/frontend/"), settings(warn_only=True):
      local("npm run build-prod-nofiles")
      #local("npm run build-dev")
  else:
    print ("buildings...just prod")
    with lcd(WORKING_DIR + "/web/frontend/"), settings(warn_only=True):
      local("npm run build-prod")
      #local("npm run build-dev")


  with lcd(WORKING_DIR), settings(warn_only=True):
    local("git add .")
    local("git commit -m '" + str(commit_msg) + "'")
    local("git push")




def _containers_build(machine):  
  
  server_name = env.host_names[machine]
  print ("CHANGING TO " + machine + " in " + env.hosts_url[machine])
  
  with prefix('eval "$(docker-machine env ' + server_name + ')"'):    
    print("building containers for " + env.service_type + " type server (DB connection, email, etc, from .env) ...")
    local('docker-compose -f ./full_deploy_' + env.service_type + '_machine.yml build')
    local('docker-compose -f ./full_deploy_' + env.service_type + '_machine.yml up -d --force')




def git_pull_to_host(machine):
  #machine = tick, tack or worker - type of machine to work with: just tick and tack implemented
  server_name = env.host_names[machine]
  print ("CHANGING TO " + machine + " in " + env.hosts_url[machine])
  
  with lcd('[YOUR_PATH]/Code/your_codebase/'):
    local_user_email=local('git config --global user.email', capture=True)
    local_user_name=local('git config --global user.name', capture=True)


  with prefix('eval "$(docker-machine env ' + server_name + ')"'):
    local('docker exec -it devops_web_1 git config --global user.email ' + local_user_email)
    local('docker exec -it devops_web_1 git config --global user.name ' + local_user_name)
    local('docker exec -it devops_web_1 git reset --hard')        
    #with settings(warn_only=True):
    #  local("docker exec -it devops_web_1 sh -c 'rm -R /your_codebase/web/frontend/static/*'")
    with cd("/your_codebase"):
#      local('docker exec -it devops_web_1 sudo git clean  -d  -fx')    
      local('docker exec -it devops_web_1 git pull')
      local('docker exec -it devops_web_1 git add .')
      local('docker exec -it devops_web_1 git stash')
      local('docker exec -it devops_web_1 git checkout ' + env.branch)    
      local('git branch -v')
      print "docker exec -it devops_web_1 sh -c 'cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/* /your_codebase/web/frontend/static/'"      
      local("docker exec -it devops_web_1 sh -c 'cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/* /your_codebase/web/frontend/static/'")
      local('docker exec -it devops_web_1 git branch -v')
      



# def teste():
#   with lcd('~/2nd'):
#     local_user_email=local('git config --global user.email', capture=True)

def _remove_machine(host):
  local('docker-machine stop ' + host)
  local('docker-machine rm ' + host)

def install_requirements_python(machine):
  server_name = env.host_names[machine]
  with prefix('eval "$(docker-machine env ' + server_name + ')"'):
    local("docker exec -it devops_web_1 sh -c 'pip install -r requirements.txt'")

def codebase_to_static(machine):
  server_name = env.host_names[machine]
  print ("CHANGING TO " + machine + " in " + env.hosts_url[machine])
  
  with prefix('eval "$(docker-machine env ' + server_name + ')"'):
    print "docker exec -it devops_web_1 sh -c 'cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/* /your_codebase/web/frontend/static/'"
    local("docker exec -it devops_web_1 sh -c 'cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/* /your_codebase/web/frontend/static/'")
    #local("docker exec -it devops_web_1 cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/* /your_codebase/web/frontend/static/")
    #local("docker exec -it devops_web_1 cp -fR /your_codebase/web/frontend/" + env.compile_dir + "/website/ /your_codebase/web/frontend/static/")
    #local("docker exec -it devops_web_1 ln -sfT ../frontend/" + env.compile_dir + " ../frontend/static")
    #local("docker exec -it devops_web_1 rm -R ../frontend/static/")
    

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#---------------------------------- Public, small Functions --------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------



def migrate(machine):
  #machine = tick, tack or worker
  print("going to migrate DB...")

  server_name = env.host_names[machine]
  print ("CHANGING TO " + machine + " in " + env.hosts_url[machine])
  
  with prefix('eval "$(docker-machine env ' + server_name + ')"'):
    print("working with " + server_name + " ...")
    local("docker exec -it devops_web_1 python manage.py migrate")

  local("docker restart devops_web_1 devops_nginx_1")

  print("DB migrated")


def restart_services(machine):
  ''' just working on local -> give "local" as param'''
  #TODO: build this...
  print("Going to restart and start the server services...")

  server_name = env.host_names[machine]
  print ("CHANGING TO " + machine + " in " + env.hosts_url[machine])
  
  with prefix('eval "$(docker-machine env ' + server_name + ')"'):
    #local("docker-compose -f ./full_" + env.compile_type + "_deploy.yml restart")
    local("docker restart devops_web_1 devops_nginx_1")




#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#---------------------------------- Main Functions --------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------



# def deploy():
#   '''Deploy to tick in any host_name,  with  any code branch: set this in the call (see main instructions)
#   you CANNOT change the deploy type 
#   '''

#   print ("This Function makes CODE DEPLOY to dev or staging orproduction, \
#     considering optimizations and local characteristics. \
#     \n REMIND TO MAKE ADD AND COMMIT: ONLY COMMITTED ITEMS ARE SENT TO SERVERS")

#   # print ("deploying " + env.compile_type + "...are you sure (Y or n)?")
#   # deploy = raw_input(prompt)
#   # if deploy=="Y":
#   #   if len(env.host_names)>=2:
#   #     swap_DNS("tack")
#   #     git_pull_to_host("tick")
#   #     swap_DNS("tick")      
#   #     restart_services("tick") 
#   #   else:
#   #     print("no need swapping")
#   #     git_pull_to_host("tick")
#   #     restart_services("tick") 
#   # else:
#   #   print("abort deploying")

#   git_pull_to_host("tick")
#   codebase_to_static("tick")
#   restart_services("tick")       

def deploy(server):
  '''Deploy to tick or tack in any host_name,  with  any code branch: set this in the call (see main instructions)
  you CANNOT change the deploy type 
  '''

  print ("SERVER GIT CODE DEPLOY")

  git_pull_to_host(server)
  #codebase_to_static(server)
  restart_services(server)      
  

def rebuild_containers(machine):
  #review this - it is working
  '''rebuilds all containers (not the servers) - param: tick, tack, workers or other
  Usage: fab azure_dev rebuild_containers:tack
  '''

  print ("This Function rebuilds all the containers, not the Azure servers!) \
    for local/dev/staging/production, considering local characteristics")
  server_name = env.host_names[machine]
  server_url = env.hosts_url[machine]

  print ("rebuilding " + server_name + " hosted in " + server_url + "...are you sure (Y or n)?")
  rebuild = raw_input(prompt)
  if rebuild=="Y":
    print("start rebuilding...")
    # add right 
    local("chmod 400 ./Dockerfiles/certificate/id_rsa")
    #with settings(warn_only=True):
    with prefix('eval "$(docker-machine env ' + server_name + ')"'):
      _containers_build(machine)

    print("done. Now it should be updated the code and migrate. run deploy:tick or deploy:tack")
  else:
    print("abort rebuilding...")



def full_rebuild(environment,machines,server_rebuild):
  '''rebuilds all the environment containers AND the servers'''
  print ("This Function rebuilds all the environment (It builds the containers, AND the Azure servers) \
    for local/dev/staging/production, considering local characteristics")  
  if environment=="prod":  
    

    if server_rebuild == True:
      for ind,host in enumerate(hosts):
        print "going in...create servers"

        #Swap to Tack to change Tick and vice versa - last one is tick
        if ind == 0:
          swap_DNS("tick")
        else:  
          swap_DNS("tack")


        #try to delete the machine. If the machine does not exists, no worries, just continue.
        with settings(warn_only=True):
          _remove_machine(host)    

        with settings(warn_only=False):
          local(" cd [YOUR_PATH]/devops && docker-machine create -d azure \
        --azure-subscription-id='XXXXXXX' \
        --azure-subscription-cert='azure.pem' \
        --azure-docker-port=2376 " + host)
        #print "timeout creating the machine! keep going... anyway. let's see if it was created before..."
      
        print "configure the machine..."              
        local('azure vm endpoint create ' + host + ' 80')            

    for ind,host in enumerate(hosts):
      print "going in...configure machines"


      #local('docker-machine restart ' + host)      
      with settings(warn_only=False), prefix('eval "$(docker-machine env ' + host + ')"'):
        _containers_build()

      print "docker machine " + host + " created and ready in dev."

    #local('eval "$(docker-machine env docker-vm)"')


  elif environment=="staging":
    env.host_names = ['serverstagingtick', 'serverstagingtack']
    print "not done."
    #verify if exists network
    # local('azure network vnet list')

    # x = local('docker-machine url serverdev')

    # env.user = 'azure'
    # local('docker-machine create -d "azure" --azure-subscription-id="778e3d3b-d3b7-45df-82b2-682335ef1adf" --azure-subscription-cert="azure.pem" serverdev')
    # local('docker-machine restart serverdev')
    
    
    # local('azure vm endpoint create serverdev 80')

    # local('sudo nano /etc/default/docker')
    # local('--dns 8.8.8.8')
    # local('sudo restart docker')

  elif environment=="dev":
    if machines == "all":
      hosts = ['serverdevtick', 'serverdevtack']
    else: 
      hosts = eval("['" + machines + "']")

    if server_rebuild == True:
      for ind,host in enumerate(hosts):
        print "going in...create servers"

        #Swap to Tack to change Tick and vice versa - last one is tick
        if ind == 0:
          swap_DNS("tick")
        else:  
          swap_DNS("tack")


        #try to delete the machine. If the machine does not exists, no worries, just continue.
        with settings(warn_only=True):
          _remove_machine(host)    

        with settings(warn_only=False):
          local(" cd [YOUR_PATH]/devops && docker-machine create -d azure \
        --azure-subscription-id='b1f5e126-2b1c-4902-9212-c183b2ac9bec' \
        --azure-subscription-cert='azure.pem' \
        --azure-docker-port=2376 " + host)
        #print "timeout creating the machine! keep going... anyway. let's see if it was created before..."
      
        print "configure the machine..."              
        local('azure vm endpoint create ' + host + ' 80')            

    for ind,host in enumerate(hosts):
      print "going in...configure machines"


      #local('docker-machine restart ' + host)      
      with settings(warn_only=False), prefix('eval "$(docker-machine env ' + host + ')"'):
        _containers_build()

      print "docker machine " + host + " created and ready in dev."

    #local('eval "$(docker-machine env docker-vm)"')

  else:
    print "no local env."  

#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#---------------------------------- DB Functions --------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------



def DB_initialize(environment):
  local("docker exec devops_web_1 python initialize.py")

#@task  
def DB_export(environment):
  print"oi"
  if environment == "dev":
    DB_user = local("cat ../web/.env_aws | grep DB_USER", capture=True).rsplit("=")[1]
    DB_pass = local("cat ../web/.env_aws | grep DB_PASS", capture=True).rsplit("=")[1]
    DB_name = local("cat ../web/.env_aws | grep DB_NAME", capture=True).rsplit("=")[1]    
    DB_conn = local("cat ../web/.env_aws | grep DB_CONN_STRING", capture=True).rsplit("=")[1]    
    filename = "dev_" + time.strftime("%Y%m%d-%H%M%S") + ".sql"
    pathname = "../DBlocalbkups/"

    print "dump to disk ... dump name " + filename
    local("mysqldump --host " + DB_conn + " --user " + DB_user + " -p" + DB_pass + " " + DB_name + " > " + pathname + filename)
    #local("/Applications/Postgres.app/Contents/Versions/9.4/bin/pg_dump -h " + DB_conn + " -U " + DB_user + " -d "+ DB_name + " -F c -b -v -f " + pathname + filename + ".dump")
    return pathname + filename

  if environment == "local":
    DB_user = local("cat ../web/.env_local_docker | grep DB_USER", capture=True).rsplit("=")[1]
    DB_pass = local("cat ../web/.env_local_docker | grep DB_PASS", capture=True).rsplit("=")[1]
    DB_name = local("cat ../web/.env_local_docker | grep DB_NAME", capture=True).rsplit("=")[1]    
    DB_conn = local("cat ../web/.env_local_docker | grep DB_CONN_STRING", capture=True).rsplit("=")[1]    
    filename = "dev_" + time.strftime("%Y%m%d-%H%M%S") + ".sql"
    pathname = "../DBlocalbkups/"

    print "dump to disk ... dump name " + filename
    local("mysqldump --host " + DB_conn + " --user " + DB_user + " -p" + DB_pass + " " + DB_name + " > " + pathname + filename)
    #local("/Applications/Postgres.app/Contents/Versions/9.4/bin/pg_dump -h " + DB_conn + " -U " + DB_user + " -d "+ DB_name + " -F c -b -v -f " + pathname + filename + ".dump")
    return pathname + filename


def DB_local_docker_import(filename):
  DB_user = local("cat ../web/.env_local_docker | grep DB_USER", capture=True).rsplit("=")[1]
  DB_pass = local("cat ../web/.env_local_docker | grep DB_PASS", capture=True).rsplit("=")[1]
  DB_name = local("cat ../web/.env_local_docker | grep DB_NAME", capture=True).rsplit("=")[1]    
  DB_conn_local = "192.168.59.103"

  pathname = "../DBlocalbkups/"
  print "import to boot2docker postgres instance..."

  try:
    local("mysqladmin -h " + DB_conn_local + " -u " + DB_user + " -p create " + DB_name)
  except:
    print"DB already created"

  local("mysql -h " + DB_conn_local + " -u " + DB_user + " -p " + DB_name + " < " + pathname + filename)  

def DB_local_import(filename):
  DB_user = local("cat ../web/.env_local | grep DB_USER", capture=True).rsplit("=")[1]
  DB_pass = local("cat ../web/.env_local | grep DB_PASS", capture=True).rsplit("=")[1]
  DB_name = local("cat ../web/.env_local | grep DB_NAME", capture=True).rsplit("=")[1]    
  DB_conn_local = "localhost"

  pathname = "../DBlocalbkups/"
  print "import to boot2docker postgres instance..."

  try:
    local("mysqladmin -h " + DB_conn_local + " -u " + DB_user + " -p create " + DB_name)
  except:
    print"DB already created"

  local("mysql -h " + DB_conn_local + " -u " + DB_user + " -p " + DB_name + " < " + pathname + filename)  


def DB_dev_to_local_docker():
  '''get DB from dev and use it in local'''

  print"get DB from dev and use it in local!"
  filename = DB_export("dev")    
  DB_local_import(filename)




#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------
#---------------------------------- OTHER Functions --------------------------------------
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------




def swap_DNS(docker = "tick"):
  """Use case: fab azure_prod swap_DNS:tack"""

  print ("SWAP DNS Pointers to ...")  

  
  
  serverURL = env.hosts_url[docker]
  
  api = _DynectRest()


  DYN_CUSTOMER_NAME = local("cat ../web/.env | grep DYN_CUSTOMER_NAME", capture=True).rsplit("=")[1]
  DYN_USERNAME = local("cat ../web/.env | grep DYN_USERNAME", capture=True).rsplit("=")[1]    
  DYN_PASS = local("cat ../web/.env | grep DYN_PASS", capture=True).rsplit("=")[1]    


  # Log in dyndns
  arguments = {
      'customer_name': DYN_CUSTOMER_NAME,
      'user_name': DYN_USERNAME,
      'password': DYN_PASS,
  }
  print "arguments: " + str(arguments)
  response = api.execute('/Session/', 'POST', arguments)
  print "login: " + str(response)

  if response['status'] != 'success':
      sys.exit("Incorrect credentials")

  # # Perform change cname
  response = api.execute('CNAMERecord/daialogue.com/www.daialogue.com/', 'GET')
  cname_id = response['data'][0].rsplit("/")[-1]

  print "name to PUT: " + serverURL + " - " + cname_id
  args = {"rdata" : {'cname': serverURL}, 'ttl': '30',}
  response = api.execute('CNAMERecord/daialogue.com/www.daialogue.com/'+cname_id, 'PUT', args)
  print "PUT: " + str(response)

#  response = api.execute('CNAMERecord/server.com/www.server.com/', 'GET')
#  print "RESULT: " + str(response)

  args2 = {'publish': '1',}

  response = api.execute('Zone/daialogue.com', 'PUT', args2)
  print "RESULT_zone_publish: " + str(response)


  # Log out, to be polite
  api.execute('/Session/', 'DELETE')



def get_current_DNS():
  """Use case: fab azure_prod swap_DNS:tack"""

  print ("get DNS name ...")  

  api = _DynectRest()


  DYN_CUSTOMER_NAME = local("cat ../web/.env | grep DYN_CUSTOMER_NAME", capture=True).rsplit("=")[1]
  DYN_USERNAME = local("cat ../web/.env | grep DYN_USERNAME", capture=True).rsplit("=")[1]    
  DYN_PASS = local("cat ../web/.env | grep DYN_PASS", capture=True).rsplit("=")[1]    


  # Log in dyndns
  arguments = {
      'customer_name': DYN_CUSTOMER_NAME,
      'user_name': DYN_USERNAME,
      'password': DYN_PASS,
  }
  print "arguments: " + str(arguments)
  response = api.execute('/Session/', 'POST', arguments)
  print "login: " + str(response)

  if response['status'] != 'success':
      sys.exit("Incorrect credentials")

  response = api.execute('CNAMERecord/daialogue.com/www.daialogue.com/', 'GET')
  cname_id = response['data'][0].rsplit("/")[-1]

  response = api.execute('CNAMERecord/daialogue.com/www.daialogue.com/'+cname_id, 'GET')
  print "CURRENT SERVER: " + str(dict(response)["data"]["rdata"]["cname"])


# def restart_services(environment):
#   print ("This Function restart services like nginx, Django, etc. \
#     for local/dev/staging/production")
#   if environment=="prod":
#     print ("rebuilding production...are you sure (Y or n)?")
#     rebuild = raw_input(prompt)
#     if rebuild=="Y":
#       print("start rebuilding prod...")

#     else:
#       print("abort rebuilding prod")
#   elif environment=="dev":
#     print("start rebuilding dev...")

#   elif environment=="staging":
#     print("start rebuilding staging...")
#     # local('eval "$(docker-machine env serverdev)"')
#     # local('docker-compose -f ./full_dev_deploy.yml build')
#     # local('docker-compose -f ./full_dev_deploy.yml up -d')
#     # local('eval "$(docker-machine env docker-vm)"')
#     print("no staging env ...yet!")



