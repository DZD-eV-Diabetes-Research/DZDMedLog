#!/bin/bash

OWNER="$(id -u):$(id -g)"
PYPROJECT="MedLog/backend/pyproject.toml"
BACKEND="MedLog/backend"

docker run --rm \
    -v "$(pwd)":/app \
    -w /app \
    python:latest bash -c "
        python -m pip install --user pip-tools -U &&

        rm -f $BACKEND/requirements.txt &&
        python -m piptools compile -o $BACKEND/requirements.txt $PYPROJECT &&
        chown $OWNER $BACKEND/requirements.txt $PYPROJECT &&

        rm -f $BACKEND/requirements_tests.txt &&
        python -m piptools compile --extra=tests -o $BACKEND/requirements_tests.txt $PYPROJECT &&
        chown $OWNER $BACKEND/requirements_tests.txt
        rm -f $BACKEND/requirements_docs.txt &&
        python -m piptools compile --extra=docs -o $BACKEND/requirements_docs.txt $PYPROJECT
        chown $OWNER $BACKEND/requirements_docs.txt
    "
