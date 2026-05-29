#!/usr/bin/env bash

#######################################
# Start MedLog Tests with SQLITE DB
#######################################
PYTHON_BIN=$(which python)
echo "Start tests with Python: $PYTHON_BIN"

export SQL_DATABASE_URL="sqlite+aiosqlite:///MedLog/backend/tests/testdb.sqlite"
"$PYTHON_BIN" -m pytest MedLog/backend/tests "$@"
