#!/usr/bin/env bash

POSTGRES_CONTAINER_NAME=medlog-testing-postgres
POSTGRES_USER=medlog
POSTGRES_PW=123456
POSTGRES_PORT=5432


pg_docker_ready() {
  local attempts="${2:-30}" i=0
  echo "Checking PostgreSQL in '$POSTGRES_CONTAINER_NAME'..."
  while [[ $((i++)) -lt $attempts ]]; do
    docker exec "$POSTGRES_CONTAINER_NAME" pg_isready -U postgres &>/dev/null && echo "✓ Postgres Ready" && return 0
    sleep 1
  done
  echo "✗ Timeout after $attempts attempts"
  return 1
}


docker stop $POSTGRES_CONTAINER_NAME
docker rm $POSTGRES_CONTAINER_NAME
docker run -d --name $POSTGRES_CONTAINER_NAME -e POSTGRES_PASSWORD=$POSTGRES_PW -e POSTGRES_USER=$POSTGRES_USER -e POSTGRES_DB=$POSTGRES_USER -p $POSTGRES_PORT:5432 docker.io/library/postgres:12-alpine
export SQL_DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PW@localhost:$POSTGRES_PORT/$POSTGRES_USER"

pg_docker_ready
echo ""
echo "# POSTGRES BOOTED"
echo ""
# Detect Python binary
PYTHON_BIN=$(which python)
echo "Start tests with Python: $PYTHON_BIN"


#######################################
# Start MedLog Tests with Postgres
#######################################
"$PYTHON_BIN" ./MedLog/backend/tests/main.py 
docker stop $POSTGRES_CONTAINER_NAME
echo "Postgres stopped but not removed. If you want to inspect the db run"
echo ""
echo "docker start $POSTGRES_CONTAINER_NAME"
echo ""
echo "you can conenct to the postgres db with $SQL_DATABASE_URL"

