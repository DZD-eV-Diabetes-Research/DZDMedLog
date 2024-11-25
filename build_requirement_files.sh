#!/bin/bash
python -m pip install pip-tools -U

rm MedLog/backend/requirements.txt
python -m piptools compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml

rm MedLog/backend/requirements_tests.txt
python -m piptools compile --extra=tests -o MedLog/backend/requirements_tests.txt MedLog/backend/pyproject.toml

rm MedLog/backend/requirements_docs.txt
python -m piptools compile --extra=docs -o MedLog/backend/requirements_docs.txt MedLog/backend/pyproject.toml
