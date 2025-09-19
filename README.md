
> [!WARNING]  
> Under heavy development. Do not use yet.

# DZDMedLog

A Webapplication to log medication history of study participants.

> [!IMPORTANT]  
> MedLog requires you to bring your own drug database. As these are always licensed, we can not include a drug database in MedLog.
> (But there is a small dummy database integrated by default for developement or demos)

- [DZDMedLog](#dzdmedlog)
- [Run](#run)
  - [Option 1: Run prebuild container from docker hub](#option-1-run-prebuild-container-from-docker-hub)
  - [Option 2: Run from local build Container](#option-2-run-from-local-build-container)
  - [Option 3: Run from Local Source](#option-3-run-from-local-source)
- [Development](#development)
  - [Branches](#branches)
    - [Subbranches](#subbranches)
  - [Start local developing](#start-local-developing)
    - [1. Setup Server/Backend Dev Environment](#1-setup-serverbackend-dev-environment)
    - [2. Setup Client/Frontend Environment](#2-setup-clientfrontend-environment)
    - [3. Start the DZDMedlog backend server with a OIDC dummy server](#3-start-the-dzdmedlog-backend-server-with-a-oidc-dummy-server)
      - [3b. Reset the backend](#3b-reset-the-backend)
    - [4.](#4)
- [Config](#config)

# Run

> [!IMPORTANT]  
> these examples set DZDMedLog into demo mode. This sidesteps the need to create a config file first.
> For a more elaborate config see the chapter [Config](#config)

## Option 1: Run prebuild container from docker hub

Requirements:

- docker

Get or Update the container IMAGE

`docker pull dzdde/dzdmedlog`

Run the container

`docker run -v ./database:/opt/medlog/data -p 8888:8888 -e DEMO_MODE=true dzdde/dzdmedlog`


visit http://localhost:8888

## Option 2: Run from local build Container

> [!IMPORTANT]  
> We assume you run DZDMedLog under Linux. If you run a different OS you may need to adapt this instructions at certain points.

Requirements:

- docker runable as non root (If you use `sudo docker` have a look into `build_docker.sh` and adapt the command)

`make container`

`docker run -v ./database:/opt/medlog/data -p 8888:8888 -e DEMO_MODE=true dzdmedlog`

visit http://localhost:8888

## Option 3: Run from Local Source

> [!IMPORTANT]  
> We assume you run DZDMedLog under Linux. If you run a different OS you may need to adapt this instructions at certain points.

Requirements:

- bun or npm
- python 3.11 or higher (Tip: create a python virtual env if you like too)

Install Server dependencies

`pip install -U -r MedLog/backend/requirements.txt`

Build frontend

`bun install && bunx nuxi generate` or `npm install && npx nuxi generate`

Run the app:

`export DEMO_MODE=true`

`python MedLog/backend/medlogserver/main.py`

visit http://localhost:8888


# Development

> [!IMPORTANT]  
> We assume you develope under Linux. If you run a different OS you may need to adapt this instructions at some points.

## Branches

We have to primary branches in this Repo

[`dev`](https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/tree/dev) - This branch is always the most recent running version. On every commit there will be a new container image build automaticly. The container image will have with the tags `dev` and a version string (e.g. `0.11.1.dev2_g0e169a8e3.d20250916`)
[`main`](https://github.com/DZD-eV-Diabetes-Research/DZDMedLog) - This is the "production grade" branch building the source of new [releases](https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/releases). When we are happy with the state of dev we merge `dev` into  `main` and create a new release.

> [!NOTE]  
> There maybe a third primarty test/staging branch at a later stage when DZDMedLog enters into maintenance phase.


### Subbranches

For active developlemt we use temporary subbranches. These are seperated into 4 sub pathes according to their nature:

* `refactor/*` 
* `feature/*` 
* `fix/*` 
* `experiment/*`

The branch path name-part should begin with `issue-XX` acording to the issue it related to and short human readable identifier.

e.g. `refactor/issue-41-new-auth-mech` or `fix/issue-129-fix-worker-crash`

When a subbranch development is finished it get merged into dev to build a new container image for testing.

## Start local developing

### 1. Setup Server/Backend Dev Environment

We need to ensure the right python version and all python modules we need are installed to run and work on the server.  
The most convienient way to prepare the server environment is to use our script for that.  
  
Start a terminal and run tha bash script:  
```bash
build_server_dev_env.sh
```

> [!WARNING]  
> This will install [`uv`](https://docs.astral.sh/uv/) on your system to manage python versions and the python virtual env.
> If you dont want that have a look at the chapter [Run.Local Source](#local-source) on how to install the python modules yourself.

### 2. Setup Client/Frontend Environment

We need to ensure the a usable Java-/TypeScript runtime, toolkit, package manager,... is available.
If you are happy with bun you can just use our bash script to prepar the development environment for the client

Start a terminal and run tha bash script:  
```bash
build_client_dev_env.sh
```

> [!WARNING]  
> This will install [`bun`](https://docs.astral.sh/uv/) on your system to manage Nuxt and other ts/js modules.
> You also can choose another manager tool. You just need to run a `<youToolOfChoice> install` in `MedLog/frontend`

### 3. Start the DZDMedlog backend server with a OIDC dummy server

To start the backend server with a OIDC Mockup server as authentication source use the bash script:

```bash
run_dev_backend_server_with_oidc.sh
```

This way you can start developing without the need for any configuration

#### 3b. Reset the backend

If you want to start with a fresh backend instance just stop the server, delete `local.sqlite` and run `run_dev_backend_server_with_oidc.sh` again.


### 4. 

Now we can start the nuxt dev server

`cd MedLog/frontend`

`bun run dev`

visit http://localhost:3000 for the client

and

visist http://localhost:8888/docs to see the API Documentation

# Config

for all possible configuration parameters see [config.py](MedLog/backend/medlogserver/config.py)


> [!IMPORTANT]  
> This chaper still needs to be written :) sorry
