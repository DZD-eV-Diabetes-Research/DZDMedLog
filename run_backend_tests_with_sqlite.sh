#!/usr/bin/env bash

#######################################
# Start MedLog Tests with SQLITE DB
#######################################
PYTHON_BIN=$(which python)
echo "Start tests with Python: $PYTHON_BIN"

export SQL_DATABASE_URL="sqlite+aiosqlite:///testdb.sqlite"
"$PYTHON_BIN" ./MedLog/backend/tests/main.py 
