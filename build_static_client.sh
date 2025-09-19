#!/bin/bash
# Create static frontend files so the python FastApi backend can server the client without the need of an extra node.js server

docker pull oven/bun 
docker run -it --user $(id -u):$(id -g) -v ./MedLog/openapi.json:/openapi.json -v ./MedLog/frontend:/app oven/bun /bin/sh -c "cd /app && bun install && bunx nuxi generate"
# wrong file linke because it was made in docker
rm ./MedLog/frontend/dist
ln -s .output/public ./MedLog/frontend/dist