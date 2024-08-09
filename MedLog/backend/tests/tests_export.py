from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)


def test_do_export():
    res = req(
        "study/b6f2c61b-d388-4412-8c9a-461ece251116/export",
        method="post",
        q={"format": "json"},
    )
    dict_must_contain(
        res,
        required_keys=["state"],
        exception_dict_identifier="create export object",
    )
    processing_export = True
    while processing_export:
        res = req(
            f"study/b6f2c61b-d388-4412-8c9a-461ece251116/export/{res['export_id']}",
            method="get",
        )
        if res["state"] not in ["queued", "running"]:
            processing_export = False
            continue
        time.sleep(0.5)
    res = req(
        f"study/b6f2c61b-d388-4412-8c9a-461ece251116/export/{res['export_id']}/download",
        method="get",
    )
    print(res)
