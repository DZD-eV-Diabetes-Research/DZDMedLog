#!/usr/bin/env bash
set -euo pipefail

# === CONFIGURATION ===
PYTHON_VERSION="3.11"
ENV_DIR=".medlogcondaenv"
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
        exit 1
    fi
}

# === MAIN SCRIPT ===

install_uv
create_env
activate_env
install_requirements

echo "✅ Setup complete. Virtual environment is ready at $ENV_DIR (Python $PYTHON_VERSION)"

echo "You can now use the script "
echo ""
echo "     ./run_dev_backend_server_with_oidc.sh"
echo ""
echo "to start the DZDMedLog server."

