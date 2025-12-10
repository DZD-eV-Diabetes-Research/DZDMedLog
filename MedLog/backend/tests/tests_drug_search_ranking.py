from typing import Any, List, Dict, cast
import json
from _single_test_file_runner import run_all_tests_if_test_file_called
import time
import datetime

if __name__ == "__main__":
    run_all_tests_if_test_file_called()

from utils import (
    req,
    dict_must_contain,
    dictyfy,
    create_test_study,
    TestDataContainerStudy,
)


def test_endpoint_drug_search_ranking():
    """Test GET /api/drug/search"""
    from medlogserver.api.routes.routes_drug import search_drugs

    search_term = "Search Many"
    response: Dict[str, Any] = req(
        "api/drug/search", method="get", q={"search_term": search_term}
    )

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="search result response",
    )
    assert len(response["items"]) > 0
    first_search_result = response["items"][0]

    dict_must_contain(
        first_search_result,
        required_keys=["drug_id", "relevance_score", "drug"],
        exception_dict_identifier="first_search_result response",
    )
    first_search_result_drug_name = first_search_result["drug"]["trade_name"]
    print(
        f"relevance_score for '{search_term}' on drug '{first_search_result_drug_name}'",
        first_search_result["relevance_score"],
    )
    assert first_search_result["relevance_score"] > 1
