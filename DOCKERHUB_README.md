# DZDMedLog

A Webapplication to log medication history of studyparticipants.

For more details visit: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog

# Run

## Prebuild container

Get or Update the container image

`docker pull dzdde/dzdmedlog`

Run the container

`docker run -v ./database:/opt/medlog/data -p 8888:8888 -e DEMO_MODE=true dzdde/dzdmedlog`

(Alternatively) If you have a WiDo GKV Arzneimittelindex to hand:

`docker run -v ./database:/opt/medlog/data ./GKV_AI_StammPlus:/opt/medlog/arzneimittelindex -p 8888:8888 -e DEMO_MODE=true dzdde/dzdmedlog`

visit http://localhost:8888

for a local build:

`docker run -v ./database:/opt/medlog/data -v ./GKV_AI_StammPlus:/opt/medlog/arzneimittelindex -p 8888:8888 -e DRUG_TABLE_PROVISIONING_SOURCE_DIR=/opt/medlog/arzneimittelindex/202301 -e DEMO_MODE=true --rm <image_name>`