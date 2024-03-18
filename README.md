# YSOF API

## Create virtual environment
```
cd current directory
virtualenv .venv --python=python3.9
```
## Install packages
### Ubuntu
```
source .venv/bin/activate
pip install -r requirements.txt
```
### Window
```
.venv\Scripts\activate
pip install -r requirements.txt
```

### Update requirements file:

```
pip freeze > requirements.txt
```

## Copy environment
```
cp .env-example .env
```

## Run API
sh scripts/start-dev.sh

## Unitest - Require before every commit
```
cp .env-example .test.env
pytest -x
```

## Format code - precommit
```
pip install pre-commit
pip install ruff
```

## Run docker-compose
```
cp .<ENVIRONMENT>.env .env
sh scripts/deploy.sh <ENVIRONMENT> <BRANCH>
sh scripts/stop-docker.sh <ENVIRONMENT>
```

## Connect to mongodb running on docker
```
docker exec -it b3be3312dcdb mongosh -u "<username>" -p "<password>"
mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1
```

## Backup mongodb on Docker
```
docker exec -i <CONTAINER_ID> /usr/bin/mongodump --username "<username>" --password "<password>" --authenticationDatabase admin --db ysof --archive > ysof.dump
```

## Restore mongodb to Docker
```
docker exec -i <CONTAINER_ID> /usr/bin/mongorestore --username ""<username>" --password "<password>" --authenticationDatabase admin --nsInclude="ysof.*" --archive < ~/Downloads/ysof.dump
```
