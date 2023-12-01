#!/bin/bash
docker compose -f docker-compose.local-demo.yml down --remove-orphans &&
    docker compose -f docker-compose.local-demo.yml build &&
    docker compose -f docker-compose.local-demo.yml up -d
