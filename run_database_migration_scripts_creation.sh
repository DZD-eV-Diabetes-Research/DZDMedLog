#!/usr/bin/env bash

set -e
TARGET_DIR=./MedLog/backend/medlogserver/

# Default message is empty
MESSAGE=""

# Parse optional -m flag
while getopts m: flag; do
    case "${flag}" in
        m) MESSAGE="${OPTARG}" ;;
    esac
done

# If no message provided, fetch latest git commit message
if [ -z "$MESSAGE" ]; then
    GIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "no commit message")
    MESSAGE="Automated migration: ${GIT_MSG}"
fi

echo "Running alembic command:"
echo "alembic revision --autogenerate -m \"$MESSAGE\""

(cd $TARGET_DIR && alembic revision --autogenerate -m "$MESSAGE")