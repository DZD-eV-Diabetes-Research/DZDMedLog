
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



OIDC_COOKIE_SECRET=devdummyvalue1345
OIDC_CLIENT_ID=devdummyvalue1345
OIDC_SERVER_METADATA_URL=http://localhost:8884/.well-known/openid-configuration


# using somewhat akward EOF/heredoc for dogding even more akward escaping
export AUTH_OIDC_PROVIDERS=$(cat <<EOF
[{"PROVIDER_SLUG_NAME": "mockup-server-oidc", "PROVIDER_DISPLAY_NAME":"Mockup Server OIDC","CLIENT_ID":"${OIDC_CLIENT_ID}","CLIENT_SECRET":"${OIDC_COOKIE_SECRET}","DISCOVERY_ENDPOINT":"${OIDC_SERVER_METADATA_URL}"}]
EOF
)
echo "Kill zombie processes..."
kill_processes_by_path oidc_provider_mock_server.py

echo "Start dummy OIDC Provider"
# boot OIDC mockup authenticaion server
(cd ./MedLog/backend/medlogserver/_dev && python3 oidc_provider_mock_server.py) &
mock_server_PID=$!

# Wait up to 3 seconds for oidc mockup server to boot successfull
for i in {1..3}; do
    if ! kill -0 $mock_server_PID 2>/dev/null; then
        # Process has exited, check its exit code
        echo "OIDC mockup server failed to start."
        exit 1
    fi
    sleep 1
done
echo "OIDC mockup server seemed to have booted."
PIDS+=($mock_server_PID)  # Store PID
# Boot MedLog Backend
python3 ./MedLog/backend/medlogserver/main.py & 
PIDS+=($!)  # Store PID of last background process
wait
