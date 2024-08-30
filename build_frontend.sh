#!/bin/bash
# bun install && bun run build &&
docker run -it --user $(id -u):$(id -g) -v ./MedLog/frontend:/app oven/bun /bin/sh -c "cd /app && bun install && bunx nuxi generate"
# wrong file linke because it was made in docker
rm ./MedLog/frontend/dist
ln -s .output/public ./MedLog/frontend/dist