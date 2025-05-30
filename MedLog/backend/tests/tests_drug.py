from typing import List, Dict
import json
import time
import uuid
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    dictyfy,
    create_test_study,
    TestDataContainerStudy,
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


# import only as IDE Shortcut
import medlogserver.api.routes.routes_drug

from medlogserver.model.drug_data.drug import (
    DrugCustomCreate,
    DrugValApiCreate,
    DrugCodeApi,
    DrugValRef,
    DrugMultiValApiCreate,
)
from medlogserver.model.drug_data.drug import DrugData


def test_custom_drug_incomplete():
    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
        DrugValApiCreate,
        DrugCodeApi,
        DrugValRef,
        DrugValMulti,
        DrugMultiValApiCreate,
        DrugVal,
    )
    from medlogserver.model.drug_data.drug import DrugData, DrugValMultiRef, DrugValRef

    search_identifiert_flag = "SEARCHIDENTIFIERT328794623"
    custom_drug_payload = DrugCustomCreate(
        trade_name=f"Look mom, my custom Drug! {search_identifiert_flag}",
        attrs_ref=[DrugValRef(field_name="dispensingtype", value=None)],
    )

    res = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(custom_drug_payload),
    )
    print("res", res)
    dict_must_contain(
        res,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
        },
        exception_dict_identifier="create minimal custom drug object",
    )

    # lets look up our new drug
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req(
        f"/api/drug/search", method="get", q={"search_term": search_identifiert_flag}
    )
    print("drug_search_result", drug_search_result)
    drug_id_from_search = drug_search_result["items"][0]["drug_id"]
    assert drug_id_from_search == res["id"]


def test_create_custom_drug_with_refs():
    """Test creating a custom drug with reference values"""
    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug

    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name="My Custom Drug",
        codes=[DrugCodeApi(code_system_id="PZN", code="12345678910")],
        attrs=[
            DrugValApiCreate(field_name="amount", value="100"),
            DrugValApiCreate(field_name="manufacturer", value="Company1"),
        ],
        attrs_ref=[
            DrugValApiCreate(field_name="dispensingtype", value="0"),
        ],
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="producing_country", values=["UK", "DE"])
        ],
    )
    print("custom_drug_payload", custom_drug_payload)
    res = req(
        "api/drug/custom",
        method="post",
        b=custom_drug_payload.model_dump(exclude_unset=True),
    )
    print("res", res)
    dict_must_contain(
        res,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
            "custom_drug_notes": custom_drug_payload.custom_drug_notes,
            "is_custom_drug": True,
        },
        required_keys=["codes", "attrs", "attrs_multi_ref"],
        exception_dict_identifier="create custom drug object",
    )
    dict_must_contain(
        res["attrs_ref"],
        required_keys_and_val={
            "dispensingtype": {
                "value": 0,
                "display": "prescription",
                "ref_list": "/api/drug/field_def/dispensingtype/refs",
            }
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["attrs_multi_ref"],
        required_keys_and_val={
            "producing_country": [
                {
                    "value": "UK",
                    "display": "United Kingdom",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
                {
                    "value": "DE",
                    "display": "Germany",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
            ]
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["codes"],
        required_keys_and_val={"PZN": "12345678910"},
        exception_dict_identifier="create custom drug object attrs_ref",
    )


def test_create_custom_drug_with_multi_values():
    """Test creating a custom drug with multi-value attributes"""
    search_identifiert_flag = "SEARCHIDENTIFIERT328794623"
    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name=f"My Custom Drug {search_identifiert_flag}",
        codes=[DrugCodeApi(code_system_id="PZN", code="654643534534")],
        attrs=[
            DrugValApiCreate(field_name="amount", value="100"),
            DrugValApiCreate(field_name="manufacturer", value="MyHomeLab"),
        ],
        attrs_ref=[
            DrugValApiCreate(field_name="dispensingtype", value="0"),
        ],
        attrs_multi=[
            DrugMultiValApiCreate(
                field_name="keywords", value=["homemade", "custom", "test"]
            ),
        ],
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="producing_country", values=["DE", "UK"])
        ],
    )

    res = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(custom_drug_payload),
    )
    print("res", res)
    dict_must_contain(
        res,
        required_keys_and_val={
            "trade_name": custom_drug_payload.trade_name,
            "custom_drug_notes": custom_drug_payload.custom_drug_notes,
            "is_custom_drug": True,
        },
        required_keys=["codes", "attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref"],
        exception_dict_identifier="create custom drug object",
    )

    dict_must_contain(
        res["attrs_ref"],
        required_keys_and_val={
            "dispensingtype": {
                "value": 0,
                "display": "prescription",
                "ref_list": "/api/drug/field_def/dispensingtype/refs",
            }
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["attrs_multi_ref"],
        required_keys_and_val={
            "producing_country": [
                {
                    "value": "DE",
                    "display": "Germany",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
                {
                    "value": "UK",
                    "display": "United Kingdom",
                    "ref_list": "/api/drug/field_def/producing_country/refs",
                },
            ]
        },
        exception_dict_identifier="custom drug attrs_multi_ref",
    )
    dict_must_contain(
        res["codes"],
        required_keys_and_val={"PZN": "654643534534", "ATC": None},
        exception_dict_identifier="create custom drug object attrs_ref",
    )

    # lets look up our new drug
    from medlogserver.api.routes.routes_drug import search_drugs

    drug_search_result = req(
        f"/api/drug/search", method="get", q={"search_term": search_identifiert_flag}
    )
    print("drug_search_result", drug_search_result)
    drug_id_from_search = drug_search_result["items"][0]["drug_id"]
    assert drug_id_from_search == res["id"]


def test_endpoint_drug_search():
    """Test GET /api/drug/search endpoint"""
    from medlogserver.api.routes.routes_drug import search_drugs

    # Search for drugs
    search_query = "test"
    response = req("api/drug/search", method="get", q={"search_term": search_query})

    dict_must_contain(
        response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="search drugs response",
    )
    from medlogserver.api.routes.routes_drug import MedLogSearchEngineResult

    # Each drug result should have required fields
    for drug in response["items"]:
        dict_must_contain(
            drug,
            required_keys=["drug_id", "drug", "relevance_score"],
            exception_dict_identifier="drug search result item",
        )

    # Test empty search
    error_response = req(
        "api/drug/search",
        method="get",
        q={"search_term": ""},
        tolerated_error_body={
            "detail": [
                {
                    "type": "string_too_short",
                    "loc": ["query", "search_term"],
                    "msg": "String should have at least 3 characters",
                    "input": "",
                    "ctx": {"min_length": 3},
                }
            ]
        },
    )

    # Test pagination
    paginated_response = req(
        "api/drug/search",
        method="get",
        q={"search_term": search_query, "limit": 3, "offset": 0},
    )
    assert len(paginated_response["items"]) <= 3


def test_endpoint_drug_get():
    """Test GET /api/drug/id/{drug_id} endpoint"""
    # First search for a drug to get an ID
    search_response = req("api/drug/search", method="get", q={"search_term": "Test"})
    dict_must_contain(
        search_response,
        required_keys=["total_count", "offset", "count", "items"],
        exception_dict_identifier="search drugs response",
    )
    drug_id = search_response["items"][0]["drug_id"]
    drug_by_search = search_response["items"][0]["drug"]
    # Get drug by ID
    drug_by_id = req(f"api/drug/id/{drug_id}", method="get")

    assert drug_by_search == drug_by_id

    # Test non-existent drug ID
    non_existent_id = str(uuid.uuid4())
    req(
        f"api/drug/id/{non_existent_id}",
        method="get",
        expected_http_code=404,
        tolerated_error_codes=[404],
    )
