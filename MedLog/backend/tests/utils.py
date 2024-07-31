from typing import Dict, Literal
import os
import requests
from medlogserver.config import Config

MEDLOG_ACCESS_TOKEN_ENV_NAME = "MEDLOG_ACCESS_TOKEN"


def get_access_token() -> str | None:
    return os.environ.get(MEDLOG_ACCESS_TOKEN_ENV_NAME, None)


medlogserver_config = Config()


def get_medlogserver_base_url():

    return f"http://{medlogserver_config.SERVER_LISTENING_HOST}:{medlogserver_config.SERVER_LISTENING_PORT}"


def authorize(user, pw):
    response = req("auth/token", f={"username": user, "password": pw})
    """response example:
    {
    "token_type": "Bearer",
    "expires_in": 59999,
    "expires_at": 1722483261,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTViMjgxNy00ODE3LTRjM2UtOTA5My03OGI3ZjFkNDI4NjgiLCJleHAiOjE3MjMwMjgwNjEsImF1ZCI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODg4OC8iLCJpc3MiOiJsb2NhbGhvc3Q6ODg4OCIsImlkIjoiNWYwMTgxZTgtNzMyNy00MzgzLWE1ZDUtYzZhN2ExNDc2NDAxIiwiaWF0IjoxNzIyNDIzMjYxLjMzMDU5NH0.CwHThLnhFDiHUpqzn7e5A0zRP_0ndOsGWGEH6es3byE",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTViMjgxNy00ODE3LTRjM2UtOTA5My03OGI3ZjFkNDI4NjgiLCJleHAiOjE3MjI0ODMyNjEsImlhdCI6MTcyMjQyMzI2MSwiYXVkIjoibG9jYWxob3N0IiwiaXNzIjoibG9jYWxob3N0Ojg4ODgiLCJ1c2VyIjoie1wiZGlzcGxheV9uYW1lXCI6bnVsbCxcImNyZWF0ZWRfYXRcIjpcIjIwMjQtMDctMzBUMTM6MjE6MjIuMjMyNzM0XCIsXCJyb2xlc1wiOltcIm1lZGxvZy1hZG1pblwiXSxcInVzZXJfbmFtZVwiOlwiYWRtaW5cIixcImVtYWlsXCI6XCJ1c2VyQHRlc3QuZGVcIixcImlkXCI6XCI0OTViMjgxNy00ODE3LTRjM2UtOTA5My03OGI3ZjFkNDI4NjhcIixcImRlYWN0aXZhdGVkXCI6ZmFsc2UsXCJpc19lbWFpbF92ZXJpZmllZFwiOmZhbHNlfSIsImlkIjoiMGUyYzMwYzctNjgwZS00ZGYxLWJjZWQtYjFkZWYxNmJiOTVmIiwicmVmcl9pZCI6IjVmMDE4MWU4LTczMjctNDM4My1hNWQ1LWM2YTdhMTQ3NjQwMSJ9.vuz_jadz2moBxnKK1uju8cEtXoDLed8nK-4cNxBDWn4",
    "refresh_token_expires_in": 604799,
    "refresh_token_expires_at": 1723028061
    }
    """
    os.environ[MEDLOG_ACCESS_TOKEN_ENV_NAME] = response["access_token"]


def req(
    endpoint: str,
    method: Literal["get", "post", "put", "patch", "delete"] = "get",
    q: Dict = None,  # query params as dict
    b: Dict = None,  # json body as dict
    f: Dict = None,  # form data as dict
    expected_http_code: int = None,
    suppress_auth: bool = False,
) -> Dict:
    http_method_func = getattr(requests, method)
    http_method_func_params = {}
    http_method_func_headers = {}
    if q:
        # query params
        http_method_func_params["params"] = q
    if b:
        # body
        http_method_func_params["json"] = b
    if f:
        # formdata
        http_method_func_headers["Content-Type"] = "application/x-www-form-urlencoded"
        http_method_func_params["data"] = f
    # url
    if endpoint and not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"
    url = f"{get_medlogserver_base_url()}{endpoint}"
    http_method_func_params["url"] = url

    # auth
    access_token = get_access_token()
    if access_token and not suppress_auth:
        http_method_func_headers["Authorization"] = f"Bearer {access_token}"

    # attach headers to request params
    if http_method_func_headers:
        http_method_func_params["headers"] = http_method_func_headers

    # create log message that documents the whole request
    log_msg_request = f"REQUEST:{method} - {endpoint} - PARAMS: {({k:v for k,v in http_method_func_params.items() if k != 'url'})} - HEADERS: {http_method_func_headers}"
    print(log_msg_request)

    # fire request
    r = http_method_func(**http_method_func_params)
    if expected_http_code:
        assert (
            r.status_code == expected_http_code
        ), f"Exptected http status {expected_http_code} got {r.status_code} for {log_msg_request}"
    else:
        r.raise_for_status()
    return r.json()
