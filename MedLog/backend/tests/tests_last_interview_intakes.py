from typing import List, Dict
import json
import time
from _single_test_file_runner import run_all_tests_if_test_file_called

if __name__ == "__main__":
    run_all_tests_if_test_file_called()
from utils import (
    req,
    dict_must_contain,
    list_contains_dict_that_must_contain,
    create_test_study,
    TestDataContainerStudy,
    is_valid_csv_with_rows,
    dictyfy,
)
from statics import (
    ADMIN_USER_EMAIL,
    ADMIN_USER_NAME,
)
import datetime


def test_last_interview_intakes():
    noise_study_data: TestDataContainerStudy = create_test_study(
        study_name="TextLastIntakesStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
    )
    study_data: TestDataContainerStudy = create_test_study(
        study_name="TextLastIntakesStudy2",
        with_events=2,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
        proband_count=1,
        deterministic=True,
    )
    proband_id = 51235
    # create interview in event2

    # end interview
    study_id = study_data.study.id
    penultimate_event = study_data.events[0]
    last_event = study_data.events[1]

    from medlogserver.api.routes.routes_interview import (
        create_interview,
        InterviewCreateAPI,
        InterviewUpdateAPI,
    )

    interview1_id = penultimate_event.interviews[0].interview.id
    interview2_id = last_event.interviews[0].interview.id
    proband_id = penultimate_event.interviews[0].interview.proband_external_id
    drug_id = str(penultimate_event.interviews[0].intakes[0].drug.id)
    interview1 = req(
        f"api/study/{study_id}/event/{penultimate_event.event.id}/interview/{interview1_id}",
        method="patch",
        b=dictyfy(
            InterviewUpdateAPI(
                interview_end_time_utc=datetime.date.today(),
            )
        ),
    )

    interview2 = req(
        f"api/study/{study_id}/event/{last_event.event.id}/interview/{interview2_id}",
        method="patch",
        b=dictyfy(
            InterviewUpdateAPI(
                interview_end_time_utc=None,
            )
        ),
    )

    from medlogserver.api.routes.routes_intake import (
        list_all_intakes_of_last_completed_interview,
    )

    last_intakes = req(
        f"api/study/{study_id}/proband/{proband_id}/interview/last/intake",
        method="get",
        q={},
    )
    print("drug_id", drug_id)
    last_intake_drug_id = last_intakes[0]["drug_id"]
    print("last_intake_drug_id ", type(last_intake_drug_id), last_intake_drug_id)
    print("drug_id             ", type(drug_id), drug_id)
    # we only have on drug in last interview
    assert len(last_intakes) == 1
    assert last_intake_drug_id == drug_id

    from medlogserver.api.routes.routes_intake import (
        list_all_intakes_of_last_completed_interview_detailed,
        IntakeDetailListItem,
    )

    last_intakes_detailed = req(
        f"api/study/{study_id}/proband/{proband_id}/interview/last/intake/details",
        method="get",
        q={},
    )
    print("last_intakes_detailed", last_intakes_detailed)
    # we only have on drug in last interview
    assert len(last_intakes_detailed) == 1
    assert last_intakes_detailed[0]["drug_id"] == drug_id
    assert last_intakes_detailed[0]["drug"]["id"] == drug_id
