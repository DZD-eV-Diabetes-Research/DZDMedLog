#!/usr/bin/env bash
# Run MedLog backend tests with SQLite. The DB file persists after the run
# at MedLog/backend/tests/testdb.sqlite for inspection.
#
# Pass --dev to stop at the first failure and show the full traceback (good for local dev).
PYTEST_ARGS=("--db=sqlite")
for arg in "$@"; do
    if [ "$arg" = "--dev" ]; then
        PYTEST_ARGS+=("-x" "-s" "--tb=long")
    else
        PYTEST_ARGS+=("$arg")
    fi
done
"$(which python)" -m pytest MedLog/backend/tests "${PYTEST_ARGS[@]}"
