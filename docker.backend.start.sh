#!/bin/sh
cleanup() {
    echo "Received signal. Cleaning up..."
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "hello world"
if [ ! -f "$SPRING_CONFIG_LOCATION" ]; then
    # config file does not exists. put a copy a template in the location.
    cp /app/config_template.properties $SPRING_CONFIG_LOCATION
fi
exec java -jar idom.jar "$@"
