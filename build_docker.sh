#/bin/bash
docker_tag=$1
if [ -z "$docker_tag" ]; then
    # default container image tag of non is provided
    docker_tag="dzdmedlog:latest"
fi
echo "Build docker image with tag '$docker_tag'"
docker build -t $docker_tag -f MedLog/backend/Dockerfile MedLog/backend/