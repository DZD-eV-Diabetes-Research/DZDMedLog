from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def list_last_intakes():
    from medlogserver.api.routes.routes_intake import (
        list_all_intakes_of_last_completed_interview,
    )

    res = req(
        "api//study/b6f2c61b-d388-4412-8c9a-461ece251116/proband/1234/interview/last/intake",
        method="get",
    )
    for intake in res:
        dict_must_contain(
            intake,
            required_keys=[
                "custom_drug_id",
                "intake_regular_or_as_needed",
                "regular_intervall_of_daily_dose",
                "administered_by_doctor",
            ],
            exception_dict_identifier="list last intake object",
        )


def test_intakes():
    list_last_intakes()
