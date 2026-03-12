#!/bin/bash
# Create static frontend files so the python FastApi backend can server the client without the need of an extra node.js server

docker pull oven/bun 


# DELETE OLD ARTIFACTS
dirs=("./MedLog/frontend/.nuxt" "./MedLog/frontend/.output" "./MedLog/frontend/dist" "./MedLog/frontend/node_modules")

auto_confirm=false

[[ "$1" == "-y" ]] && auto_confirm=true

# Filter to only existing ones
existing=()
for dir in "${dirs[@]}"; do
  [[ -d "$dir" ]] && existing+=("$dir")
done

if [[ ${#existing[@]} -gt 0 ]]; then
  echo "[INFO] The following directories will be deleted: ${existing[*]}"

  if [[ "$auto_confirm" == false ]]; then
    read -r -p "Proceed? (y/N): " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "[ABORT] Deletion cancelled."; exit 1; }
  fi

  for dir in "${existing[@]}"; do
    rm -rf "$dir" && echo "[INFO] Deleted: $dir"
  done
else
  echo "[INFO] No directories to delete, continuing..."
fi

# BUILD CLIENT
docker run -it --user $(id -u):$(id -g) -v ./MedLog/openapi.json:/openapi.json -v ./MedLog/frontend:/app oven/bun /bin/sh -c "cd /app && bun install && bunx nuxi generate"
# wrong file linke because it was made in docker
rm ./MedLog/frontend/dist



ln -s .output/public ./MedLog/frontend/dist