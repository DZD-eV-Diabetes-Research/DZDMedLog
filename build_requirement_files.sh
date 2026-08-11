#!/bin/bash
set -euo pipefail

OWNER="$(id -u):$(id -g)"
PYPROJECT="MedLog/backend/pyproject.toml"
BACKEND="MedLog/backend"

# Pin the interpreter instead of tracking `python:latest`: the resolution result depends
# on the Python version, so a moving tag silently changes the generated pins.
# Must stay >= the `requires-python` in pyproject.toml.
PYTHON_IMAGE="python:3.14"

# pip-tools (7.6.0, current latest) imports `stdlib_pkgs` from `pip._internal.utils.compat`,
# which pip 26 removed, so it crashes on import against the pip shipped in recent images.
# Keep pip below 26 until pip-tools supports it.
PIP_PIN="pip<26"

docker run --rm \
    -v "$(pwd)":/app \
    -w /app \
    "$PYTHON_IMAGE" bash -euo pipefail -c "
        # A venv keeps pip-tools and the downgraded pip off the image's system install.
        python -m venv /tmp/venv
        /tmp/venv/bin/pip install --quiet --disable-pip-version-check '$PIP_PIN'
        /tmp/venv/bin/pip install --quiet --disable-pip-version-check pip-tools

        # --upgrade makes the resolver ignore the pins already in the output file, so the
        # result is as fresh as deleting it first would be -- but a failed run leaves the
        # existing file intact instead of wiping it.
        compile() {
            local out=\"\$1\"
            shift
            /tmp/venv/bin/python -m piptools compile --upgrade \"\$@\" -o \"\$out\" '$PYPROJECT'
            chown '$OWNER' \"\$out\"
        }

        compile '$BACKEND/requirements.txt'
        compile '$BACKEND/requirements_tests.txt' --extra=tests
        compile '$BACKEND/requirements_docs.txt' --extra=docs
    "
