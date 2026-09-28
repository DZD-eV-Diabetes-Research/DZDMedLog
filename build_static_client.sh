#!/bin/bash
# Create static frontend files so the python FastApi backend can server the client without the need of an extra node.js server

docker pull node:24
docker run -it --rm -v ./MedLog/openapi.json:/openapi.json:ro -v ./MedLog/frontend:/app-ro:ro -v ./MedLog/frontend/.output:/tmp/output node:24 /bin/sh -c "cp -r /app-ro /app && cd /app && npm ci && npm run generate && mv /app/.output/public /tmp/output/public && chown --recursive \"$(id -u):$(id -g)\" /tmp/output"

