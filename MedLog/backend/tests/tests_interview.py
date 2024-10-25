from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def list_interviews():
    from medlogserver.api.routes.routes_interview import list_all_interviews_of_study

    res = req(
        "/study/b6f2c61b-d388-4412-8c9a-461ece251116/interview",
        method="get",
    )
    for interview in res:
        dict_must_contain(
            interview,
            required_keys=["proband_external_id", "event_id"],
            exception_dict_identifier="list interview object",
        )


def test_interview():
    list_interviews()
