# https://oidc-provider-mock.readthedocs.io/latest/
from typing import List, Dict
import oidc_provider_mock
from oidc_provider_mock import User
import logging
import time
import requests
from pathlib import Path

import yaml

CONFIG_DATABASE_FILE = Path(Path(__file__).parent, "oidc_testusers.yaml")


def provision_test_users(oidc_mockup_server_base_url: str):
    users: List[Dict] = []
    if CONFIG_DATABASE_FILE.is_file():
        with open(CONFIG_DATABASE_FILE, "r") as file:
            file_content_parsed = yaml.safe_load(file.read())
            if "users" in file_content_parsed:
                users.extend(file_content_parsed["users"])
    for user in users:
        print(f"Create testuser data: {user}")
        res = requests.put(
            f"{oidc_mockup_server_base_url}/users/{user['sub']}",
            json=user,
        )
        res.raise_for_status()


def get_test_users() -> List[User]:
    users: List[Dict] = []
    if CONFIG_DATABASE_FILE.is_file():
        with open(CONFIG_DATABASE_FILE, "r") as file:
            file_content_parsed = yaml.safe_load(file.read())
            if "users" in file_content_parsed:
                users.extend(file_content_parsed["users"])
    result_users: List[User] = []
    for user in users:
        print(f"Create testuser data: {user}")
        result_users.append(User(sub=user["sub"], claims=user))
    return result_users


def start_oidc_server_thread(port: int = 8884):

    with oidc_provider_mock.run_server_in_thread(
        port=port,
        user_claims=get_test_users(),
    ) as server:
        server_url = f"http://localhost:{server.server_port}"
        print(f"OIDC Provider Mockup Server listening at {server_url}")
        # provision_test_users(server_url)
        try:
            if __name__ == "__main__":
                print("Press Ctrl+C to exit the loop.")

            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Exiting the loop safely.")


if __name__ == "__main__":
    start_oidc_server_thread()
