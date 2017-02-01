# Devops boilerplate for docker images in azure (or AWS) using fabric

A simple 2-docker machines balanced for development/production to reduce downtimes and make clean deployments, with automatic git pull for containers.

- This code is based on docker, docker-compose, docker-machine, fabric

- It is able to control a nginx server, postgres server or mysql (default), a backend based on python and static files depoyment (react.js was used in this case)

- It creates dev and prod environments with 2 balanced docker machines: tick and tack, similar, one for prod the other used in preprod, for instance.







How to 

### Run Like this:
```
    fab [host_name] compile_type:[compile_type] branch_name:[branch] <instruction>
```
###Examples:

deploy usage:
```    
    1st) fab git_push ou fab git_push:False (no build, just push)
    2nd) fab azure_prod compile_type:prod branch_name:dev deploy:tack swap_DNS:tack
```
Other funcs:

```
    1) fab azure_prod rebuild_containers:tack (rebuilds from scratch all containers (not the servers))
    2) fab azure_prod restart_services:tack 
    3) fab azure_prod full_rebuild (rebuilds all the environment containers AND the servers)
    4) fab azure_prod compile_type:prod branch_name:TEST1 codebase_to_static:tack
    5) fab azure_prod swap_DNS:tack
```

fab azure_dev compile_type:prod branch_name:dev deploy:tack or deploy:tick swap_DNS:tack



###Instructions
##############
```
[host_name] = [azure_dev, azure_prod, local_docker]
```

this affects where to deploy - and what machines to deploy
also, service_type that is, what type of services: email pass, DB (prod or dev) etc. (from .env files)
see their definitions


##############
```
[compile_type] = [prod, dev, shared_code...]
```

compilation type: 
this affects compilation type prod and dev (static code and django), 
and code deploy through shared directory (shared_code) or else, through git

##############
```
[branch_name] = [prod, dev, other...] 
```

- what to deploy

<instruction> - deploy:tick, deploy:tack, etc (see available with fab --list)

don't forget to prepare your branch (commit, add and pull should be done!) 
git merge develop --no-ff





###RULES
 
- There should be 1 .env file per host_name which defines their local configurations
- *static* is the folder where active code is - fabfile copy to there the code for deploy.

####Service_type - defines type of services, e.g. DB, email, django app secret key, etc 
(info from .env_XXX, added in docker compose (yml) to the machine)
service type is what choose the kind of yml for docker compose. since full_[prod]_deploy.yml are the 
rules for [prod, dev, staging] type of service to install - 
this is changed with the service type.
'''


#### Important

- Substitute variables to use in fabfile - denoted with XXXXXXX
- Substitute with [YOUR_PATH] in fabfile
- Substitute with your_codebase in serveral files.
- Substitute with your_server in serveral files.


