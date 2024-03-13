#/bin/bash
docker_tag=$1
if [ -z "$docker_tag" ]; then
    # default container image tag of non is provided
    docker_tag="dzdmedlog:latest"
fi
# write __version__.py to server module dir. While creating the container, we will strip away the .git dir that contains any meta info about the version of the module.
# thats why we manifest the version number into a module file.
python MedLog/backend/medlogserver/main.py --set_version_file

echo "Build docker image with tag '$docker_tag'"
docker build -t $docker_tag -f MedLog/backend/Dockerfile MedLog/backend/
