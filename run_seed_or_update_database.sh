#!/usr/bin/env bash


# Exit on error
set -e

# Detect Python binary
PYTHON_BIN=$(which python)
echo "Python: $PYTHON_BIN"

export LOG_LEVEL=DEBUG
export DEBUG_SQL=False
export SERVER_SESSION_SECRET=IAMASTUPIDDUMMYANDTHATSOKSDEALWITHITINEEDTOBE64CHARSLONGTHATWHYIKEEPTALKING
export ADMIN_USER_PW=password123

echo "Run Database Seeding or Migration"
echo "\"$PYTHON_BIN\" ./MedLog/backend/medlogserver/main.py --setup_database_only"
"$PYTHON_BIN" ./MedLog/backend/medlogserver/main.py --setup_database_only



