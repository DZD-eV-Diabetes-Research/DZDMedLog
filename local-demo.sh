#!/bin/bash
docker compose -f docker-compose.local-dev.yml down &&
    docker compose -f docker-compose.local-dev.yml build &&
    docker compose -f docker-compose.local-dev.yml up -d
