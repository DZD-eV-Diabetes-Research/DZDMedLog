#!/usr/bin/env bash

# Detect if being sourced
(return 0 2>/dev/null) && SOURCED=1 || SOURCED=0

if [[ $SOURCED -eq 0 ]]; then
    echo "❌ Error: This script must be sourced, not executed. Otherwise we can enable the python virtual env."
    echo "Usage: source $0"
    exit 1
fi

# Only set strict mode, but restore shell options after script completes
ORIGINAL_OPTS=$(set +o)
set -eo pipefail
# Don't use -u when sourcing to avoid breaking the parent shell

# === CONFIGURATION ===
PYTHON_VERSION="3.14"
ENV_DIR=".medlog-python-env"
REQ_FILE="./MedLog/backend/requirements.txt"
REQ_FILE_DEV="./MedLog/backend/requirements_tests.txt"

# === FUNCTIONS ===

install_uv() {
    if ! command -v uv &>/dev/null; then
        echo "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
        echo "uv installed successfully."
    else
        echo "uv already installed."
    fi
}

create_env() {
    if [[ -d "$ENV_DIR" ]]; then
        echo "Environment already exists at $ENV_DIR. Skipping creation."
    else
        echo "Creating virtual environment with Python $PYTHON_VERSION..."
        uv venv --python "$PYTHON_VERSION" "$ENV_DIR"
    fi
}

activate_env() {
    echo "🏎️ Activating environment at $ENV_DIR"
    # shellcheck disable=SC1091
    source "$ENV_DIR/bin/activate"
}

install_requirements() {
    if [[ -f "$REQ_FILE" ]]; then
        echo "Installing/Updating requirements from $REQ_FILE..."
        uv pip install --upgrade pip
        uv pip install -r "$REQ_FILE"
        echo "Installing/Updating requirements from $REQ_FILE_DEV..."
        uv pip install -r "$REQ_FILE_DEV"
    else
        echo "Requirements file not found at $REQ_FILE"
        return 1
    fi
}

# === MAIN SCRIPT ===

install_uv
create_env
activate_env
install_requirements

echo "✅ Setup complete. Virtual environment is active (Python $PYTHON_VERSION)"
echo ""
echo "You can now use the script:"
echo ""
echo "     ./run_dev_backend_server_with_oidc.sh"
echo ""
echo "to start the DZDMedLog server."

# Restore original shell options (optional, might not be necessary)
# eval "$ORIGINAL_OPTS"