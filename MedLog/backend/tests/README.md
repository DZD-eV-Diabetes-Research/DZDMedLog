# Run tests for medlogserver

API Tests: in development. not any automation yet

## options

env vars:
    * MEDLOG_TESTS_RESET_DB -> deletes the db at start of the tests and creates a new one.
* mii pharmindex

## Export benchmark

`tests_export_performance.py` contains an opt-in benchmark for the study export (issue #362).
It seeds studies with the given numbers of intake rows and prints duration, query count and
peak memory of the export before and after #362:

```bash
MEDLOG_EXPORT_BENCHMARK_ROWS=1000,10000 ./run_backend_tests_with_sqlite.sh -k test_export_benchmark -s
```

See the module docstring for the other options.
