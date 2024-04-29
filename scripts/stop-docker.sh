#!/bin/bash

set -e

env=$1
if [ -z "$1" ]
  then
    echo "Param :env is required as $1"
    exit 1
fi

echo "Remove $1 containers"
#docker-compose down --remove-orphans

CONTAINER_NAME="ysof_api_$1"; docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME
CONTAINER_NAME="ysof_mongodb_$1"; docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME
CONTAINER_NAME="ysof_celery_$1"; docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME
CONTAINER_NAME="ysof_rabbitmq_$1"; docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME

exit 0
