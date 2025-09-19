#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Checking for Bun..."

if command -v bun >/dev/null 2>&1; then
    echo "[INFO] Bun found. Updating..."
    curl -fsSL https://bun.sh/install | bash
else
    echo "[INFO] Bun not found. Installing..."
    curl -fsSL https://bun.sh/install | bash
fi

# Ensure Bun is in PATH for this session
export PATH="$HOME/.bun/bin:$PATH"

if ! command -v bun >/dev/null 2>&1; then
    echo "[ERROR] Bun installation failed or PATH not set."
    exit 1
fi

echo "[INFO] Bun version: $(bun --version)"

TARGET_DIR="./MedLog/frontend"

if [ ! -d "$TARGET_DIR" ]; then
    echo "[ERROR] Target directory $TARGET_DIR does not exist."
    exit 1
fi

echo "[INFO] Running bun install in $TARGET_DIR..."
cd "$TARGET_DIR"
bun install

echo "[INFO] bun install completed successfully in $TARGET_DIR"
