from typing import List, Dict
import json
import time
from _single_test_file_runner import run_all_tests_from_caller
from utils import req, dict_must_contain, list_contains_dict_that_must_contain, dictyfy
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


# import only as IDE Shortcut
import medlogserver.api.routes.routes_drug


def test_do_drugv2():
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
    from medlogserver.model.drug_data.drug import DrugData

    search_identifiert_flag = "SEARCHIDENTIFIERT328794623"
    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name=f"My Custom Drug {search_identifiert_flag}",
        codes=[DrugCodeApi(code_system_id="PZN", code="12345678910")],
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
        required_keys_and_val={"PZN": "12345678910", "ATC": None},
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


run_all_tests_from_caller()
