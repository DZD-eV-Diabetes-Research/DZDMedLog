# Dev

##  Install req only

`cd MedLog/backend`

`python -m pip install pip-tools`

`pip-compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml`

`pip install -r requirements.txt -U`


## FAQ

* The return to the /auth ednpoint from the Authentik OIDC provider fails with an "ValueError: Invalid key set format" error
  * I had to update the provider in authentik. seems to be an issue with the self-signed singing key in the demo env
