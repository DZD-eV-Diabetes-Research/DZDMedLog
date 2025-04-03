#!/bin/bash

docker run --rm -v "$(pwd)":/app -w /app python:latest bash -c "
python -m pip install --user pip-tools -U &&
rm -f MedLog/backend/requirements.txt &&
python -m piptools compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml &&
chown $(id -u):$(id -g) MedLog/backend/requirements.txt MedLog/backend/pyproject.toml &&
rm -f MedLog/backend/requirements_tests.txt &&
python -m piptools compile --extra=tests -o MedLog/backend/requirements_tests.txt MedLog/backend/pyproject.toml &&
chown $(id -u):$(id -g) MedLog/backend/requirements_tests.txt
rm -f MedLog/backend/requirements_docs.txt &&
python -m piptools compile --extra=docs -o MedLog/backend/requirements_docs.txt MedLog/backend/pyproject.toml
chown $(id -u):$(id -g) MedLog/backend/requirements_docs.txt
"
