#!/bin/bash

env="$1"

if [ -z "$env" ]; then 
    env="dev"
fi

# Let's make sure the folder exists
mkdir -p data/mysql-$env

docker-compose -f docker-compose.$env.yaml up --build --remove-orphans
