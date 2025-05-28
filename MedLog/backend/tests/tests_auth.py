from typing import List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import req, dict_must_contain
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_endpoint_auth_schemes_list():
    """Test GET /api/auth/schemes endpoint"""
    response = req("api/auth/schemes", method="get", suppress_auth=True)

    # Verify response contains list of auth schemes
    assert isinstance(response, list)
    for scheme in response:
        dict_must_contain(
            scheme,
            required_keys=["name", "slug", "type", "login_endpoint", "token_endpoint"],
            exception_dict_identifier="auth scheme",
        )


def test_endpoint_auth_token_create():
    """Test POST /api/auth/token endpoint"""
    response = req(
        "api/auth/token",
        method="post",
        f={"username": ADMIN_USER_NAME, "password": "admin"},
        suppress_auth=True,
    )

    dict_must_contain(
        response,
        required_keys=[
            "access_token",
            "token_type",
            "expires_in",
            "expires_at",
            "refresh_token",
            "refresh_token_expires_in",
            "refresh_token_expires_at",
        ],
        exception_dict_identifier="token response",
    )
    assert response["token_type"] == "Bearer"

    # Test invalid credentials
    req(
        "api/auth/token",
        method="post",
        f={"username": "invalid", "password": "invalid"},
        suppress_auth=True,
        expected_http_code=401,
        tolerated_error_codes=[401],
    )


def test_endpoint_auth_refresh_create():
    """Test POST /api/auth/refresh endpoint"""
    # First get a valid token
    login_response = req(
        "api/auth/token",
        method="post",
        f={"username": ADMIN_USER_NAME, "password": "admin"},
        suppress_auth=True,
    )

    # Test refresh token via form data
    refresh_response = req(
        "api/auth/refresh",
        method="post",
        f={"refresh_token": login_response["refresh_token"]},
        suppress_auth=True,
    )

    dict_must_contain(
        refresh_response,
        required_keys=["access_token", "token_type", "expires_in", "expires_at"],
        exception_dict_identifier="refresh token response",
    )

    # Test refresh token via header
    refresh_response = req(
        "api/auth/refresh",
        method="post",
        headers={"refresh-token": f"Bearer {login_response['refresh_token']}"},
        suppress_auth=True,
    )

    dict_must_contain(
        refresh_response,
        required_keys=["access_token", "token_type", "expires_in", "expires_at"],
        exception_dict_identifier="refresh token response",
    )


def test_endpoint_auth_logout_create():
    """Test POST /api/auth/logout endpoint"""
    # First get valid tokens
    login_response = req(
        "api/auth/token",
        method="post",
        f={"username": ADMIN_USER_NAME, "password": "admin"},
        suppress_auth=True,
    )

    # Test logout
    req(
        "api/auth/logout",
        method="post",
        b={"refresh_token": login_response["refresh_token"]},
        headers={"Authorization": f"Bearer {login_response['access_token']}"},
    )

    # Verify token is invalidated by trying to use it
    req(
        "api/auth/refresh",
        method="post",
        b={"refresh_token": login_response["refresh_token"]},
        suppress_auth=True,
        expected_http_code=401,
        tolerated_error_codes=[401],
    )
