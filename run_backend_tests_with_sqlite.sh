#!/usr/bin/env bash
# Run MedLog backend tests with SQLite. The DB file persists after the run
# at MedLog/backend/tests/testdb.sqlite for inspection.
"$(which python)" -m pytest MedLog/backend/tests --db=sqlite "$@"
