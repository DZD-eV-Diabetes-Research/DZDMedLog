#!/usr/bin/env bash
# Run MedLog backend tests with Postgres (via Docker).
# The container is stopped but kept after the run — see the log for reconnect instructions.
"$(which python)" -m pytest MedLog/backend/tests --db=postgres "$@"
