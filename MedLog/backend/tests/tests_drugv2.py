from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


# import only as IDE Shortcut
import medlogserver.api.routes.routes_drug_v2


def test_do_drugv2():
    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug_v2 import create_custom_drug
    from medlogserver.model.drug_data.drug import (
        DrugCustomCreate,
        DrugValApiCreate,
        DrugCodeApi,
        DrugValRef,
    )
    from medlogserver.model.drug_data.drug import DrugData

    custom_drug_payload = DrugCustomCreate(
        trade_name="myCustomDrug",
        attrs=[DrugValApiCreate(field_name="packgroesse", value="100")],
        ref_attrs=[DrugValApiCreate(field_name="hersteller", value="AABPH 01")],
        codes=[DrugCodeApi(code_system_id="PZN", code="12345678910")],
    ).model_dump(exclude_unset=True)
    print("custom_drug_payload", custom_drug_payload)
    res = req(
        "v2/drug/custom",
        method="post",
        b=custom_drug_payload,
    )
    print("res", res)
    dict_must_contain(
        res,
        required_keys_and_val={"trade_name": "myCustomDrug", "is_custom_drug": True},
        required_keys=["codes", "attrs", "ref_attrs"],
        exception_dict_identifier="create custom drug object",
    )
    dict_must_contain(
        res["ref_attrs"],
        required_keys_and_val={
            "hersteller": {
                "value": "AABPH 01",
                "display": "AAB Pharma",
                "ref_list": "/v2/drug/field_def/hersteller/refs",
            }
        },
        exception_dict_identifier="create custom drug object ref_attrs",
    )
