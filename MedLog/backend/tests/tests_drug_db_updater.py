from typing import Any, List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called
import time

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import req, dict_must_contain


def test_endpoint_drug_update_status():
    """Test GET /api/drug/db/update endpoint"""
    from medlogserver.api.routes.routes_drug_db_updater import get_drug_update_status
    from medlogserver.model.drug_updater_status import DrugUpdaterStatus

    response: Dict[str, Any] = req("api/drug/db/update", method="get")
    print(f"test_endpoint_drug_update_status response: {response}")

    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": True,
            "update_available_version": "20251228",
            "update_running": False,
            "last_update_run_error": None,
            "current_drug_data_version": "20241126",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc", "current_drug_data_version"],
        exception_dict_identifier="version response",
    )


def test_endpoint_drug_update_trigger():
    """Test GET /api/drug/db/update endpoint"""
    from medlogserver.api.routes.routes_drug_db_updater import (
        trigger_drug_update_active,
    )
    from medlogserver.model.drug_updater_status import DrugUpdaterStatus

    response: Dict[str, Any] = req("api/drug/db/update", method="put")
    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": True,
            "update_available_version": "20251228",
            "update_running": True,
            "last_update_run_error": None,
            "current_drug_data_version": "20241126",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc"],
        exception_dict_identifier="test_endpoint_drug_update_trigger response",
    )
    update_running = True
    while update_running:
        response_status: Dict[str, Any] = req("api/drug/db/update", method="get")
        print(f"test_endpoint_drug_update_trigger response_status: {response}")
        dict_must_contain(
            response_status,
            required_keys_and_val={"last_update_run_error": None},
            required_keys=["update_running"],
            exception_dict_identifier="test_endpoint_drug_update_trigger loop response",
        )
        update_running = response_status["update_running"]
        print("WAIT FOR UPDATE update_running:", update_running)
        time.sleep(2)
    response: Dict[str, Any] = req("api/drug/db/update", method="get")
    print("response", response)
    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": False,
            "update_available_version": None,
            "update_running": False,
            "last_update_run_error": None,
            "current_drug_data_version": "20251228",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc", "current_drug_data_version"],
        exception_dict_identifier="test_endpoint_drug_update_trigger response",
    )
