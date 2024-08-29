#!/bin/bash
docker run -it -v ./MedLog/frontend:/app oven/bun /bin/sh -c "cd /app && bun install && bun run build && bunx nuxi generate"