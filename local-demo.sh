#!/bin/bash
docker compose -f docker-compose.local-demo.yml down &&
    docker compose -f docker-compose.local-demo.yml build &&
    docker compose -f docker-compose.local-demo.yml up -d
