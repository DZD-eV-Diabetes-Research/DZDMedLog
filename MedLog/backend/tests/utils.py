from typing import Dict, List, Literal
import os
import requests
import json
from medlogserver.config import Config

MEDLOG_ACCESS_TOKEN_ENV_NAME = "MEDLOG_ACCESS_TOKEN"


def get_access_token() -> str | None:
    return os.environ.get(MEDLOG_ACCESS_TOKEN_ENV_NAME, None)


medlogserver_config = Config()


def get_medlogserver_base_url():

    return f"http://{medlogserver_config.SERVER_LISTENING_HOST}:{medlogserver_config.SERVER_LISTENING_PORT}"


def authorize(user, pw):
    response = req("auth/token", "post", f={"username": user, "password": pw})
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
    tolerated_error_codes: List[int] = None,
    tolerated_error_body: List[Dict | str] = None,
) -> Dict:
    if tolerated_error_codes is None:
        tolerated_error_codes = []
    if tolerated_error_body is None:
        tolerated_error_body = []
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
        try:
            r.raise_for_status()
        except requests.HTTPError as err:
            if not r.status_code in tolerated_error_codes:
                try:
                    body = r.json()
                except requests.exceptions.JSONDecodeError:
                    body = r.content
                if not body in tolerated_error_body:
                    if body:
                        print("Error body: ", body)
                    raise err
    return r.json()


def get_dot_env_file_variable(filepath: str, key: str) -> str | None:
    """
    Extracts the value of a specific environment variable from a .env file.

    Args:
        filepath (str): The path to the .env file.
        key (str): The environment variable key to look for.

    Returns:
        str | None: The value of the environment variable, or None if it's not found or empty.
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath) as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                var_key, var_value = map(str.strip, line.split("=", 1))
                if var_key == key:
                    return var_value or None
    return None


def dict_must_contain(
    d: Dict,
    required_keys_and_val: Dict = None,
    required_keys: List = None,
    raise_if_not_fullfilled: bool = True,
    exception_dict_identifier: str = None,
) -> bool:
    if required_keys_and_val is None:
        required_keys_and_val = {}
    if required_keys is None:
        required_keys = []
    for k, v in required_keys_and_val.items():
        try:
            if d[k] != v:
                if raise_if_not_fullfilled:
                    raise ValueError(
                        f"""Expected value '{v}' in key '{k}' {"in dict "+exception_dict_identifier if exception_dict_identifier else ""}' got '{d[k]}'"""
                    )
                return False
        except KeyError:
            if raise_if_not_fullfilled:
                raise KeyError(
                    f"""Expected value key '{k}' {"in dict "+exception_dict_identifier if exception_dict_identifier else ""}'"""
                )
            return False
    for k in required_keys:
        if k not in d:
            if raise_if_not_fullfilled:
                raise KeyError(
                    f"""Expected value key '{k}' {"in dict "+exception_dict_identifier if exception_dict_identifier else ""}'"""
                )
            return False
    return True


def find_first_dict_in_list(
    l: List[Dict],
    required_keys_and_val: Dict = None,
    required_keys: List = None,
    raise_if_not_found: bool = True,
    exception_dict_identifier: str = None,
) -> Dict:
    for obj in l:
        if dict_must_contain(
            obj,
            required_keys_and_val=required_keys_and_val,
            required_keys=required_keys,
            raise_if_not_fullfilled=False,
        ):
            return obj
    if raise_if_not_found:
        raise ValueError(
            f"Obj with '{required_keys_and_val}' and/or keys {required_keys} not found in {l}"
        )
    return False


def list_contains_dict_that_must_contain(
    l: List[Dict],
    required_keys_and_val: Dict = None,
    required_keys: List = None,
    raise_if_not_fullfilled: bool = True,
    exception_dict_identifier: str = None,
) -> bool:
    if find_first_dict_in_list(
        l,
        required_keys_and_val=required_keys_and_val,
        required_keys=required_keys,
        raise_if_not_found=raise_if_not_fullfilled,
        exception_dict_identifier=exception_dict_identifier,
    ):
        return True
    return False
