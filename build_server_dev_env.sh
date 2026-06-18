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

ensure_python() {
    # Make sure a *stable* CPython matching $PYTHON_VERSION is installed via uv.
    # Without this, `uv venv --python 3.14` happily reuses a previously installed
    # pre-release (e.g. 3.14.0rc2) because it already satisfies the request.
    echo "Ensuring a stable CPython $PYTHON_VERSION is installed via uv..."
    uv python install "$PYTHON_VERSION"
}

# Prints "<major.minor> <releaselevel>" for the interpreter in the venv,
# e.g. "3.14 final" or "3.14 candidate". Empty if the venv is unusable.
env_python_info() {
    "$ENV_DIR/bin/python" -c \
        'import sys; print("%d.%d %s" % (sys.version_info.major, sys.version_info.minor, sys.version_info.releaselevel))' \
        2>/dev/null || true
}

# Returns 0 (true) if the existing venv must be torn down and recreated.
needs_rebuild() {
    [[ -x "$ENV_DIR/bin/python" ]] || return 0
    local info major_minor level
    info=$(env_python_info)
    [[ -n "$info" ]] || { echo "Existing env is broken → rebuilding."; return 0; }
    major_minor=${info% *}
    level=${info#* }
    if [[ "$major_minor" != "$PYTHON_VERSION" ]]; then
        echo "Existing env is Python $major_minor, expected $PYTHON_VERSION → rebuilding."
        return 0
    fi
    if [[ "$level" != "final" ]]; then
        echo "Existing env uses a pre-release Python ($info) → rebuilding."
        return 0
    fi
    return 1
}

create_env() {
    ensure_python
    if needs_rebuild; then
        echo "Creating virtual environment with Python $PYTHON_VERSION..."
        rm -rf "$ENV_DIR"
        uv venv --python "$PYTHON_VERSION" "$ENV_DIR"
    else
        echo "Environment at $ENV_DIR already matches stable Python $PYTHON_VERSION. Skipping creation."
    fi

    # Stubborn final check: never proceed on a pre-release interpreter.
    local level
    level=$(env_python_info)
    level=${level#* }
    if [[ "$level" != "final" ]]; then
        echo "❌ venv still on a pre-release Python ($(env_python_info))."
        echo "   A stray pre-release is shadowing the stable build. Remove it and retry:"
        echo "       uv python list --only-installed"
        echo "       uv python uninstall <the rc/beta version>"
        return 1
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