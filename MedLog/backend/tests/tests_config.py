from typing import List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called
import os

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
    print("version_parts", version_parts)
    assert len(version_parts) >= 3, (
        "Version should have at least major.minor.patch format"
    )

    # Verify branch name
    assert isinstance(response["branch"], str)


def test_endpoint_config_branding_get():
    """Test GET /api/config/version endpoint"""
    response = req("api/config/branding", method="get")
    configured_support_email = os.environ.get("BRANDING_SUPPORT_EMAIL_ADDRESS")
    dict_must_contain(
        response,
        required_keys_and_val={"support_email": configured_support_email},
        exception_dict_identifier="version response",
    )
