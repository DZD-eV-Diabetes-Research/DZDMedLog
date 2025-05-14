from typing import List, Dict
import json
import time
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()
from utils import req, dict_must_contain, list_contains_dict_that_must_contain, dictyfy
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


# import only as IDE Shortcut
import medlogserver.api.routes.routes_drug


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
