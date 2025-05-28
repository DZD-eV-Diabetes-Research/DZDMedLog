from typing import List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import req, dict_must_contain


def test_endpoint_config_version_get():
    """Test GET /api/config/version endpoint"""
    response = req("api/config/version", method="get")

    dict_must_contain(
        response,
        required_keys=["version", "branch"],
        exception_dict_identifier="version response",
    )

    # Verify version format (should be semantic versioning)
    assert isinstance(response["version"], str)
    version_parts = response["version"].split(".")
    assert len(version_parts) >= 2, "Version should have at least major.minor format"
    assert all(
        part.isdigit() for part in version_parts
    ), "Version parts should be numeric"

    # Verify branch name
    assert isinstance(response["branch"], str)
