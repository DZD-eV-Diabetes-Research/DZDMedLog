from typing import List, Dict
import json
import time
from utils import req, dict_must_contain, list_contains_dict_that_must_contain, dictyfy
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)
import datetime


def last_interview_intakes():
    proband_id = "5678"

    from medlogserver.model.study import StudyCreateAPI
    from medlogserver.api.routes.routes_study import create_study

    study = req(
        "/study",
        method="post",
        b=StudyCreateAPI(display_name="MedikationsübernahmeTest").model_dump(
            exclude_unset=True
        ),
    )
    study_id = study["id"]

    from medlogserver.model.event import EventCreateAPI
    from medlogserver.api.routes.routes_event import create_event

    event1 = req(
        f"/study/{study_id}/event",
        method="post",
        b=EventCreateAPI(name="event1", order_position=1).model_dump(
            exclude_unset=True
        ),
    )
    event1_id = event1["id"]
    event2 = req(
        f"/study/{study_id}/event",
        method="post",
        b=EventCreateAPI(name="event2", order_position=2).model_dump(
            exclude_unset=True
        ),
    )
    event2_id = event2["id"]

    from medlogserver.model.interview import InterviewCreateAPI
    from medlogserver.api.routes.routes_interview import create_interview

    interview1 = req(
        f"/study/{study_id}/event/{event1_id}/interview",
        method="post",
        b=InterviewCreateAPI(
            proband_external_id=proband_id, proband_has_taken_meds=True
        ).model_dump(exclude_unset=True),
    )
    interview1_id = interview1["id"]

    from medlogserver.api.routes.routes_drug_v2 import search_drugs

    drug_search_result = req(
        f"/v2/drug/search", method="get", q={"search_term": "aspi"}
    )
    print("drug_search_result", drug_search_result)
    drug_id = drug_search_result["items"][0]["drug_id"]

    from medlogserver.model.intake import IntakeCreateAPI, ConsumedMedsTodayAnswers
    from medlogserver.api.routes.routes_intake import create_intake

    intake = req(
        f"/study/{study_id}/interview/{interview1_id}/intake",
        method="post",
        b=dictyfy(
            IntakeCreateAPI(
                drug_id=drug_id,
                intake_start_time_utc=datetime.date.today(),
                consumed_meds_today=ConsumedMedsTodayAnswers.UNKNOWN,
                as_needed_dose_unit=None,
            )
        ),
    )
    from medlogserver.model.interview import InterviewUpdate, InterviewUpdateAPI
    from medlogserver.api.routes.routes_interview import update_interview

    # end interview
    interview1 = req(
        f"/study/{study_id}/event/{event1_id}/interview/{interview1_id}",
        method="patch",
        b=dictyfy(
            InterviewUpdateAPI(
                interview_end_time_utc=datetime.date.today(),
            )
        ),
    )
    # create interview in event2
    interview2 = req(
        f"/study/{study_id}/event/{event2_id}/interview",
        method="post",
        b=dictyfy(
            InterviewCreateAPI(
                proband_external_id=proband_id, proband_has_taken_meds=True
            )
        ),
    )

    from medlogserver.api.routes.routes_intake import (
        list_all_intakes_of_last_completed_interview,
    )

    last_intakes = req(
        f"/study/{study_id}/proband/{proband_id}/interview/last/intake",
        method="get",
        q={},
    )

    # we only have on drug in last interview
    assert len(last_intakes) == 1
    assert last_intakes[0]["drug_id"] == drug_id

    from medlogserver.api.routes.routes_intake import (
        list_all_intakes_of_last_completed_interview_detailed,
        IntakeDetailListItem,
    )

    last_intakes_detailed = req(
        f"/study/{study_id}/proband/{proband_id}/interview/last/intake/details",
        method="get",
        q={},
    )
    print("last_intakes_detailed", last_intakes_detailed)
    # we only have on drug in last interview
    assert len(last_intakes_detailed) == 1
    assert last_intakes_detailed[0]["drug_id"] == drug_id
    assert last_intakes_detailed[0]["drug"]["id"] == drug_id


def test_interview():
    last_interview_intakes()
