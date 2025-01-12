#!/bin/bash

set -e

env=$1
if [ -z "$1" ]
  then
    echo "Param :env is required as $1"
    exit 1
fi

echo "Overwriting .env.$1 to .env"
rm -rf .env
cp ".env.$1" .env

if [ ! -f keyfile ]; then
  # If the keyfile does not exist, create it
  openssl rand -base64 756 > keyfile
  chmod 600 keyfile
  sudo chown 999 keyfile
  sudo chgrp 999 keyfile
  echo "Keyfile created and permissions set."
else
  # If the keyfile exists, skip the creation process
  echo "Keyfile already exists, skipping creation."
fi

echo "Rebuild docker"
docker compose -p "ysof_$1" -f docker-compose.yml -f "docker-compose.$1.yml" up -d --build

echo "Deployed branch $1"
if [ "$1" = "local" ]
  then
    echo "Clear docker cache"
    docker system prune -f
fi
exit 0
