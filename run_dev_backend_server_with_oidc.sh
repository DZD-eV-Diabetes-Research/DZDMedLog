#!/usr/bin/env bash
# Run the MedLog Backend Server with an OIDC Mockup server
# Mainly intended for Development

# Exit on error
set -e


# Control background worker spawning
RUN_BACKGROUND_WORKER_IN_EXTRA_JOB=True

#######################################
# MedLog Server Configuration
#######################################

# To overwrite this values just create `.env` in your local `MedLog/backend/medlogserver` dir and set the environment variables o you liking
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

PROVIDER_DISPLAY_NAME="LocalDevLogin"
CONFIGURATION_ENDPOINT=http://localhost:8884/.well-known/openid-configuration
CLIENT_ID=devdummyid1345
CLIENT_SECRET=devdummysecrect1345
USER_NAME_ATTRIBUTE=name
USER_DISPLAY_NAME_ATTRIBUTE=given_name
USER_MAIL_ATTRIBUTE=email
USER_GROUPS_ATTRIBUTE=groups
TOKEN_STORAGE_SECRET=asuizfqwhj

# Using EOF/heredoc to avoid excessive escaping
export AUTH_OIDC_PROVIDERS=$(cat <<EOF
[{"AUTO_LOGIN": true, "PROVIDER_DISPLAY_NAME": "${PROVIDER_DISPLAY_NAME}","CONFIGURATION_ENDPOINT":"${CONFIGURATION_ENDPOINT}","CLIENT_ID":"${CLIENT_ID}","CLIENT_SECRET":"${CLIENT_SECRET}","USER_NAME_ATTRIBUTE":"${USER_NAME_ATTRIBUTE}","USER_DISPLAY_NAME_ATTRIBUTE":"${USER_DISPLAY_NAME_ATTRIBUTE}","USER_MAIL_ATTRIBUTE":"${USER_MAIL_ATTRIBUTE}","USER_GROUPS_ATTRIBUTE": "${USER_GROUPS_ATTRIBUTE}"}, 
{"PROVIDER_DISPLAY_NAME": "${PROVIDER_DISPLAY_NAME} Nr 2","CONFIGURATION_ENDPOINT":"${CONFIGURATION_ENDPOINT}","CLIENT_ID":"${CLIENT_ID}","CLIENT_SECRET":"${CLIENT_SECRET}","USER_NAME_ATTRIBUTE":"${USER_NAME_ATTRIBUTE}","USER_DISPLAY_NAME_ATTRIBUTE":"${USER_DISPLAY_NAME_ATTRIBUTE}","USER_MAIL_ATTRIBUTE":"${USER_MAIL_ATTRIBUTE}","USER_GROUPS_ATTRIBUTE": "${USER_GROUPS_ATTRIBUTE}"}]
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
        kill "$PID" 2>/dev/null || true  # Kill process and suppress errors if already terminated
    done
    wait  # Ensure all processes exit before cleanup completes
    echo "Cleanup done."
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


# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM






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
"$PYTHON_BIN" ./MedLog/backend/medlogserver/main.py $1 &
PIDS+=($!)


#######################################
# Start Background Worker (optional)
#######################################
if [[ "${RUN_BACKGROUND_WORKER_IN_EXTRA_JOB}" =~ ^([Yy][Ee][Ss]|[Yy]|1|[Tt][Rr][Uu][Ee])$ ]]; then
    echo "Start Background worker in extra process"
    "$PYTHON_BIN" ./MedLog/backend/medlogserver/main.py --run_worker_only $1 &
    PIDS+=($!)
fi


#######################################
# Wait for all processes
#######################################
wait
