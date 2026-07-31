#!/usr/bin/env bash
set -euo pipefail

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

echo "[INFO] Checking for nvm..."

if command -v nvm >/dev/null 2>&1; then
    echo "[INFO] nvm found. Updating..."
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash
else
    echo "[INFO] nvm not found. Installing..."
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash
fi

if ! command -v nvm >/dev/null 2>&1; then
    echo "[ERROR] nvm installation failed or nvm not loaded."
    exit 1
fi

echo "[INFO] nvm version: $(nvm --version)"

TARGET_DIR="./MedLog/frontend"

if [ ! -d "$TARGET_DIR" ]; then
    echo "[ERROR] Target directory $TARGET_DIR does not exist."
    exit 1
fi

echo "[INFO] Setting up Node.js in $TARGET_DIR..."
cd "$TARGET_DIR"
nvm install
nvm use

echo "[INFO] Running npm install in $TARGET_DIR..."
npm install

echo "[INFO] npm install completed successfully in $TARGET_DIR"
