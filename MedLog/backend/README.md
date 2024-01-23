# Dev

##  Install req only

`cd MedLog/backend`

`python -m pip install pip-tools`

`pip-compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml`

`pip install -r requirements.txt -U`