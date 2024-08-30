# DZDMedLog

A Webapplication to log medication history of studyparticipants.
Uses https://www.wido.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/ as Drug database (Not included here)
(The usage if the GKV-Arzneimittelindex will change in near futur due to licensing issues with the usecase in this project)

Current Status: Development/Alpha

- [DZDMedLog](#dzdmedlog)
- [Run](#run)
  - [Prebuild container](#prebuild-container)
  - [Local Container](#local-container)
  - [Local Source](#local-source)
- [Config](#config)
- [Developement](#developement)
  - [Client Dev](#client-dev)
  - [Server Dev](#server-dev)


# Run

## Prebuild container

Requirements:
* docker

Get or Update the container image

`docker pull dzdde/dzdmedlog`

Run the container

`docker run -v ./database:/opt/medlog/data -p 8888:8888 -e DEMO_MODE=true dzdde/dzdmedlog`

If you have a WiDo GKV Arzneimittelindex to hand:

`docker run -v ./database:/opt/medlog/data ./my_arzneimittelindex:/opt/medlog/arzneimittelindex -p 8888:8888 -e DEMO_MODE=true dzdde/dzdmedlog`

visit http://localhost:8888

## Local Container

Requirements:  
* docker runable as non root (If you use `sudo docker` have a look into `build_docker.sh` and adapt the command)

`make container`

`docker run -v ./database:/opt/medlog/data -p 8888:8888 -e DEMO_MODE=true dzdmedlog`

visit http://localhost:8888

## Local Source

Requirements:  
* bun or npm
* python 3.11

Install Server dependencies

`pip install -U -r MedLog/backend/requirements.txt`

Build frontend

`bun install && bunx nuxi generate`

Run the app:

`python visit MedLog/backend/medlogserver/main.py`

visit http://localhost:8888


# Config

for all possible configuration parameters see [config.py](MedLog/backend/medlogserver/config.py)

# Developement


## Client Dev

Reqs:  
* [bun](https://bun.sh/docs/installation#installing)
* [docker](https://docs.docker.com/engine/install/)


First we need to get up the backend server running for the client to communicat to.

`make container`

create the target folder for our server state

`mkdir database`

Start the server container

```bash
docker run \
    --user $(id -u):$(id -g) \
    -v ./database:/opt/medlog/data \
    -p 8888:8888 \
    -e CLIENT_URL=http://localhost:3000 \
    -e LOG_LEVEL=DEBUG \
    -e DEMO_MODE=true \
    dzdmedlog
```

Now we can start the nuxt dev server

`cd MedLog/frontend`

`bun run dev`

visit http://localhost:3000 for the client

and

visist http://localhost:8888/docs to see the API Documentation

## Server Dev

todo