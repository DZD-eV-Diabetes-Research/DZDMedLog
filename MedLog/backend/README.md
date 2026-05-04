# DZDMedLog Server

The server module for DZDMedLog, a system to document the medical history of study participant.

## Local Setup

###  Install req only


`python -m pip install pip-tools -U`

`python -m piptools compile -o MedLog/backend/requirements.txt MedLog/backend/pyproject.toml`
or
`python -m piptools compile --extra=tests -o MedLog/backend/requirements_tests.txt MedLog/backend/pyproject.toml`
or
`python -m piptools compile --extra=docs -o MedLog/backend/requirements_docs.txt MedLog/backend/pyproject.toml`


`pip install -r MedLog/backend/requirements.txt -U`
or
`pip install -r MedLog/backend/requirements_tests.txt -U`
or
`pip install -r MedLog/backend/requirements_docs.txt -U`


### FAQ

* The return to the /auth ednpoint from the Authentik OIDC provider fails with an "ValueError: Invalid key set format" error
  * I had to update the provider in authentik. seems to be an issue with the self-signed singing key in the demo env

## Run

### Run demo with pre build docker image (recomended)

`docker run -e DEMO_MODE=true dzdde/dzdmedlog-server`

### Run backend worker seperate

Start server without background worker
`docker run -v ./data:/data -e DEMO_MODE=true -e BACKGROUND_WORKER_IN_EXTRA_PROCESS=false dzdde/dzdmedlog-server`


Start extra container with background worker
`docker run -v ./data:/data -e BACKGROUND_WORKER_IN_EXTRA_PROCESS=false dzdde/dzdmedlog-server --run_worker_only`
