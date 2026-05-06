#!/usr/bin/env bash
# Run the MedLog Backend Server with an OIDC Mockup server and a PostgreSQL database
# Mainly intended for Development
#
# Usage: ./run_dev_backend_server_with_oidc_on_postgres.sh [--reset]
#   --reset  Stop and remove the existing PostgreSQL container (wiping all data), then start fresh

# Exit on error
set -e


#######################################
# Parse arguments
#######################################
RESET_DB=false
for arg in "$@"; do
    case "$arg" in
        --reset) RESET_DB=true ;;
    esac
done


# Control background worker spawning
RUN_BACKGROUND_WORKER_IN_EXTRA_JOB=True


#######################################
# PostgreSQL Configuration
#######################################
POSTGRES_CONTAINER_NAME=medlog-dev-postgres
POSTGRES_USER=medlog
POSTGRES_PW=123456
POSTGRES_PORT=5433  # use 5433 to avoid conflict with a local postgres or the test container on 5432

export SQL_DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PW@localhost:$POSTGRES_PORT/$POSTGRES_USER"


#######################################
# MedLog Server Configuration
#######################################

# To overwrite these values just create `.env` in your local `MedLog/backend/medlogserver` dir and set the environment variables to your liking
# e.g.
# ```MedLog/backend/medlogserver/.env
# LOG_LEVEL=INFO
# DEBUG_SQL=True
# ```

export LOG_LEVEL=DEBUG
export DEBUG_SQL=False
export SERVER_SESSION_SECRET=IAMASTUPIDDUMMYANDTHATSOKSDEALWITHITINEEDTOBE64CHARSLONGTHATWHYIKEEPTALKING
export SERVER_LISTENING_PORT=8888
export ADMIN_USER_PW=password123
export ADMIN_USER_EMAIL=user@test.de
export SERVER_HOSTNAME=localhost


#######################################
# OIDC Configuration
#######################################
export AUTH_OIDC_TOKEN_STORAGE_SECRET=qi3we7gaukb


export AUTH_OIDC_PROVIDERS=$(cat <<'EOF'
[
  {
    "AUTO_LOGIN": true,
    "PROVIDER_DISPLAY_NAME": "LocalDevLogin",
    "CONFIGURATION_ENDPOINT": "http://localhost:8884/.well-known/openid-configuration",
    "CLIENT_ID": "devdummyid1345",
    "CLIENT_SECRET": "devdummysecrect1345",
    "USER_NAME_ATTRIBUTE": "name",
    "USER_DISPLAY_NAME_ATTRIBUTE": "given_name",
    "USER_MAIL_ATTRIBUTE": "email",
    "USER_GROUPS_ATTRIBUTE": "groups",
    "ROLE_MAPPING": {
      "medlog-admins": ["medlog-admin"],
      "admins": ["medlog-admin"]
    },
    "STUDY_PERMISSION_MAPPING": {
      "study1": {
        "interviewer-study1": ["is_study_interviewer"]
      }
    }
  },
  {
    "PROVIDER_DISPLAY_NAME": "LocalDevLogin Nr 2",
    "CONFIGURATION_ENDPOINT": "http://localhost:8884/.well-known/openid-configuration",
    "CLIENT_ID": "devdummyid1345",
    "CLIENT_SECRET": "devdummysecrect1345",
    "USER_NAME_ATTRIBUTE": "name",
    "USER_DISPLAY_NAME_ATTRIBUTE": "given_name",
    "USER_MAIL_ATTRIBUTE": "email",
    "USER_GROUPS_ATTRIBUTE": "groups",
    "STUDY_PERMISSION_MAPPING": {
      "study1": {
        "interviewer-study1": ["is_study_interviewer"]
      }
    }
  }
]
EOF
)

# Store process IDs
PIDS=()

# Detect Python binary
PYTHON_BIN=$(which python)
echo "Python: $PYTHON_BIN"


#######################################
# Cleanup function for script termination
#######################################
cleanup() {
    echo "Stopping all processes..."
    for PID in "${PIDS[@]}"; do
        kill "$PID" 2>/dev/null || true
    done
    wait
    echo "Cleanup done."
    echo "PostgreSQL container '$POSTGRES_CONTAINER_NAME' is still running."
    echo "  Connect: $SQL_DATABASE_URL"
    echo "  Stop:    docker stop $POSTGRES_CONTAINER_NAME"
}


#######################################
# Kill processes matching a given string
# Arguments:
#   $1 - search string
#######################################
kill_processes_by_path() {
    if [[ -z "$1" ]]; then
        echo "Usage: kill_processes_by_path <search_string>"
        return 1
    fi

    local search_string="$1"
    local pids=$(ps axo pid,command | grep "$search_string" | grep -v grep | awk '{print $1}')

    if [[ -z "$pids" ]]; then
        echo "No matching processes found."
        return 0
    fi

    echo "Killing processes: $pids"
    echo "$pids" | xargs kill -9
}


#######################################
# Wait for PostgreSQL to be ready
#######################################
pg_docker_ready() {
    local attempts="${1:-30}" i=0
    echo "Waiting for PostgreSQL in '$POSTGRES_CONTAINER_NAME'..."
    while [[ $((i++)) -lt $attempts ]]; do
        docker exec "$POSTGRES_CONTAINER_NAME" pg_isready -U postgres &>/dev/null && echo "✓ Postgres ready" && return 0
        sleep 1
    done
    echo "✗ Timeout after $attempts attempts — PostgreSQL did not become ready"
    return 1
}


# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM


#######################################
# PostgreSQL container management
#######################################
if [[ "$RESET_DB" == "true" ]]; then
    echo "-- Reset requested: removing existing PostgreSQL container..."
    docker stop "$POSTGRES_CONTAINER_NAME" 2>/dev/null || true
    docker rm   "$POSTGRES_CONTAINER_NAME" 2>/dev/null || true
fi

if docker inspect "$POSTGRES_CONTAINER_NAME" &>/dev/null; then
    # Container exists — make sure it is running
    if [[ "$(docker inspect -f '{{.State.Running}}' "$POSTGRES_CONTAINER_NAME")" != "true" ]]; then
        echo "Starting existing PostgreSQL container '$POSTGRES_CONTAINER_NAME'..."
        docker start "$POSTGRES_CONTAINER_NAME"
    else
        echo "PostgreSQL container '$POSTGRES_CONTAINER_NAME' is already running."
    fi
else
    echo "Creating and starting PostgreSQL container '$POSTGRES_CONTAINER_NAME'..."
    docker run -d \
        --name "$POSTGRES_CONTAINER_NAME" \
        -e POSTGRES_PASSWORD="$POSTGRES_PW" \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_DB="$POSTGRES_USER" \
        -p "$POSTGRES_PORT":5432 \
        docker.io/library/postgres:12-alpine
fi

pg_docker_ready 30
echo ""
echo "# POSTGRES BOOTED — $SQL_DATABASE_URL"
echo ""


# Override background worker behaviour if enabled
if [[ "${RUN_BACKGROUND_WORKER_IN_EXTRA_JOB}" =~ ^([Yy][Ee][Ss]|[Yy]|1|[Tt][Rr][Uu][Ee])$ ]]; then
    export BACKGROUND_WORKER_START_IN_EXTRA_PROCESS=false
fi


#######################################
# Kill zombie processes from former runs
#######################################
echo "Kill zombie processes..."
kill_processes_by_path oidc_provider_mock_server.py
kill_processes_by_path medlogserver/main.py


#######################################
# Start OIDC mockup server
#######################################
echo "Start dummy OIDC Provider"
(
    cd ./MedLog/backend/medlogserver/_dev && "$PYTHON_BIN" oidc_provider_mock_server.py
) &
mock_server_PID=$!

# Wait up to 3 seconds for OIDC mockup server to boot successfully
for i in {1..3}; do
    if ! kill -0 $mock_server_PID 2>/dev/null; then
        echo "OIDC mockup server failed to start."
        exit 1
    fi
    sleep 1
done
echo "OIDC mockup server seemed to have booted."
PIDS+=($mock_server_PID)


#######################################
# Start MedLog Backend
#######################################
"$PYTHON_BIN" ./MedLog/backend/medlogserver/main.py &
PIDS+=($!)


#######################################
# Start Background Worker (optional)
#######################################
if [[ "${RUN_BACKGROUND_WORKER_IN_EXTRA_JOB}" =~ ^([Yy][Ee][Ss]|[Yy]|1|[Tt][Rr][Uu][Ee])$ ]]; then
    echo "Start Background worker in extra process"
    "$PYTHON_BIN" ./MedLog/backend/medlogserver/main.py --run_worker_only &
    PIDS+=($!)
fi


#######################################
# Wait for all processes
#######################################
wait
