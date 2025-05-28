from typing import List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import req, dict_must_contain


def test_endpoint_root_get():
    """Test GET / endpoint"""
    response = req("", method="get", suppress_auth=True)  # Root path

    # Response should be HTML content
    assert isinstance(response, (str, bytes))
    assert (
        "<!DOCTYPE html>" in response.decode()
        if isinstance(response, bytes)
        else response
    )


def test_endpoint_static_files_get():
    """Test GET /{path_name} endpoint for static files"""
    # Test CSS file
    response = req("css/app.css", method="get", suppress_auth=True)
    assert isinstance(response, (str, bytes))

    # Test JS file
    response = req("js/app.js", method="get", suppress_auth=True)
    assert isinstance(response, (str, bytes))

    # Test JSON file
    response = req("manifest.json", method="get", suppress_auth=True)
    assert isinstance(response, (str, bytes))

    # Test non-existent file (should return index.html for SPA routing)
    response = req("non-existent-path", method="get", suppress_auth=True)
    assert isinstance(response, (str, bytes))
    assert (
        "<!DOCTYPE html>" in response.decode()
        if isinstance(response, bytes)
        else response
    )

    # Test invalid _nuxt path (should return 404)
    req(
        "_nuxt/non-existent",
        method="get",
        suppress_auth=True,
        expected_http_code=404,
        tolerated_error_codes=[404],
    )
