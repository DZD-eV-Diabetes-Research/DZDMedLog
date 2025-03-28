
# Run the MedLog Backend Server with a OIDC Mockup server
# This mainly intended for Frontend OIDC Development

#exit on error
set -e
# Store process IDs
PIDS=()
# Function to handle script termination
cleanup() {
    echo "Stopping all processes..."
    for PID in "${PIDS[@]}"; do
        kill "$PID" 2>/dev/null || true  # Kill process and suppress errors if already terminated
    done
    wait  # Ensure all processes exit before cleanup completes
    echo "Cleanup done."
}

kill_processes_by_path() {
    if [[ -z "$1" ]]; then
        echo "Usage: kill_processes_by_path <search_string>"
        return 1
    fi

    local search_string="$1"

    # Find processes matching the search string and extract their PIDs
    local pids=$(ps axo pid,command | grep "$search_string" | grep -v grep | awk '{print $1}')

    if [[ -z "$pids" ]]; then
        echo "No matching processes found."
        return 0
    fi

    # Kill each process
    echo "Killing processes: $pids"
    echo "$pids" | xargs kill -9
}


# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

DOT_ENV_FILE_PATH=./bbapprove/.env
if ! [ -f $DOT_ENV_FILE_PATH ]; then
echo "Create dummy '${DOT_ENV_FILE_PATH}' file"
cat >$DOT_ENV_FILE_PATH <<EOL
OIDC_COOKIE_SECRET=devdummyvalue1345
OIDC_CLIENT_ID=devdummyvalue1345
OIDC_CLIENT_SECRET=devdummyvalue1345
OIDC_SERVER_METADATA_URL=http://localhost:8884/.well-known/openid-configuration
EOL
fi
export LOG_LEVEL=DEBUG
export DOT_ENV_FILE_PATH=.env
echo "Kill zombie processes..."
kill_processes_by_path oidc_provider_mock_server.py

echo "Start dummy OIDC Provider"
# boot OIDC mockup authenticaion server
(cd ./bbapprove/_dev/ && pdm run oidc_provider_mock_server.py) &
PIDS+=($!)  # Store PID of last background process
# Boot streamlit app
(cd ./bbapprove && pdm run main.py) & 
PIDS+=($!)  # Store PID of last background process
wait
