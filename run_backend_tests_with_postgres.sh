#!/usr/bin/env bash
# Run MedLog backend tests with Postgres (via Docker).
# The container is stopped but kept after the run — see the log for reconnect instructions.
#
# Pass --dev to stop at the first failure and show the full traceback (good for local dev).
PYTEST_ARGS=("--db=postgres")
for arg in "$@"; do
    if [ "$arg" = "--dev" ]; then
        PYTEST_ARGS+=("-x" "-s" "--tb=long")
    else
        PYTEST_ARGS+=("$arg")
    fi
done
"$(which python)" -m pytest MedLog/backend/tests "${PYTEST_ARGS[@]}"
