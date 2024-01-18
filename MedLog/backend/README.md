# Dev

##  Install req only

`cd MedLog/backend`

`python -m pip install pip-tools`

`pip-compile -o requirements.txt pyproject.toml`

`pip install -r requirements.txt`