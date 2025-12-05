#!/usr/bin/env bash

#######################################
# Start MedLog Tests with SQLITE DB
#######################################
export SQL_DATABASE_URL="sqlite+aiosqlite:////testdb.sqlite"
"$PYTHON_BIN" ./MedLog/backend/tests/main.py 
