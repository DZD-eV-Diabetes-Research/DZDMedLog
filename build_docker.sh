#/bin/bash
# usage: ./build_docker.sh [--no-cache] [<docker_tag>]
docker_tag=""
no_cache=""
for arg in "$@"; do
    case "$arg" in
    --no-cache)
        # rebuild every layer from scratch, ignoring the docker build cache
        no_cache="--no-cache"
        ;;
    *)
        if [ -z "$docker_tag" ]; then
            docker_tag="$arg"
        fi
        ;;
    esac
done
if [ -z "$docker_tag" ]; then
    # default container image tag of non is provided
    docker_tag="dzdmedlog:latest"
fi
echo "Build docker image with tag '$docker_tag'"
# --pull: always check the registry for newer base images, so a rebuild picks up
# upstream patch updates to the pinned node/python tags instead of reusing a
# stale locally cached copy
docker build . -t $docker_tag --progress=plain --pull $no_cache -f Dockerfile

echo "Docker image produced: $docker_tag"
echo "Run with:"
echo "     docker run $docker_tag"
