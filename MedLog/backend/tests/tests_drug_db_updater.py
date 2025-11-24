from typing import List, Dict
import json
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import req, dict_must_contain


def test_endpoint_drug_update_status():
    """Test GET /api/drug/db/update endpoint"""
    from medlogserver.api.routes.routes_drug_db_updater import get_drug_update_status
    from medlogserver.model.drug_updater_status import DrugUpdaterStatus

    response = req("api/drug/db/update", method="get")
    print(f"test_endpoint_drug_update_status response: {response}")

    dict_must_contain(
        response,
        required_keys_and_val={
            "update_available": True,
            "update_available_version": "20241126",
            "update_running": True,
            "last_update_run_error": None,
            "current_drug_data_version": "20241126",
            "current_drug_data_ready_to_use": True,
        },
        required_keys=["last_update_run_datetime_utc", "current_drug_data_version"],
        exception_dict_identifier="version response",
    )
