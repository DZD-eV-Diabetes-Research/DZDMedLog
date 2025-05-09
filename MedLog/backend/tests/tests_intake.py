from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain
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
        DrugMultiValApiCreate,
    )
    from medlogserver.model.drug_data.drug import DrugData

    custom_drug_payload = DrugCustomCreate(
        custom_drug_notes="Look mom, my custom Drug!",
        trade_name="My Custom Drug",
        codes=[DrugCodeApi(code_system_id="PZN", code="12345678910")],
        attrs=[
            DrugValApiCreate(field_name="amount", value="100"),
            DrugValApiCreate(field_name="ist_verhuetungsmittel", value="true"),
        ],
        attrs_ref=[
            DrugValApiCreate(field_name="hersteller", value="225"),
            DrugValApiCreate(field_name="darreichungsform", value="AMP"),
            DrugValApiCreate(field_name="diaetetikum", value="E"),
        ],
        attrs_multi_ref=[
            DrugMultiValApiCreate(field_name="keywords", values=["1", "4"])
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
            "hersteller": {
                "value": "225",
                "display": "Hexal AG",
                "ref_list": "/api/drug/field_def/hersteller/refs",
            }
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["attrs_multi_ref"],
        required_keys_and_val={
            "keywords": [
                {
                    "value": 1,
                    "display": "Mund, Zähne",
                    "ref_list": "/api/drug/field_def/keywords/refs",
                },
                {
                    "value": 4,
                    "display": "Munddesinfizientien",
                    "ref_list": "/api/drug/field_def/keywords/refs",
                },
            ]
        },
        exception_dict_identifier="create custom drug object attrs_ref",
    )
    dict_must_contain(
        res["codes"],
        required_keys_and_val={"ATC": None, "PZN": "12345678910", "MMIP": None},
        exception_dict_identifier="create custom drug object attrs_ref",
    )
