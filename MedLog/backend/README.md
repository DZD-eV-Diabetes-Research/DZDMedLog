# Local Setup and running

##  Install req only


`python -m pip install pip-tools -U`

`python -m piptools compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml`

`pip install -r MedLog/backend/requirements.txt -U`


## FAQ

* The return to the /auth ednpoint from the Authentik OIDC provider fails with an "ValueError: Invalid key set format" error
  * I had to update the provider in authentik. seems to be an issue with the self-signed singing key in the demo env


## Run with docker
