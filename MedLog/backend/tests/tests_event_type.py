"""Event types per interview and the external event ID (issue #388).

The test server runs with `EVENT_TYPES` from statics.py. The "switched off" case and
the config validation are tested in-process.
"""

from typing import Dict, Optional
import csv
import datetime
import io

import pytest
from pydantic import ValidationError

from statics import EVENT_TYPES
from utils import (
    req,
    dict_must_contain,
    create_test_study,
    TestDataContainerStudy,
)
from tests_export import _wait_for_export

ON_SITE, REMOTE, PHONE = EVENT_TYPES


def _create_event(study_id, name: str, expected_http_code: int = 200, **attrs) -> Dict:
    return req(
        f"api/study/{study_id}/event",
        method="post",
        b={"name": name, **attrs},
        expected_http_code=expected_http_code,
    )


def _create_interview(
    study_id,
    event_id,
    proband_id,
    expected_http_code: int = 200,
    **attrs,
) -> Dict:
    return req(
        f"api/study/{study_id}/event/{event_id}/interview",
        method="post",
        b={
            "proband_external_id": proband_id,
            "interview_start_time_utc": datetime.datetime.now().isoformat(),
            "proband_has_taken_meds": True,
            **attrs,
        },
        expected_http_code=expected_http_code,
    )


def _update_interview(
    study_id, event_id, interview_id, body: Dict, expected_http_code: int = 200
) -> Dict:
    return req(
        f"api/study/{study_id}/event/{event_id}/interview/{interview_id}",
        method="patch",
        b=body,
        expected_http_code=expected_http_code,
    )


def _study(name: str, proband_count: int = 6) -> TestDataContainerStudy:
    return create_test_study(
        study_name=name, with_events=0, proband_count=proband_count
    )


# ---------------------------------------------------------------- config


def test_config_event_types_validation():
    from medlogserver.config import Config

    assert Config(EVENT_TYPES=[" on-site ", "remote"]).EVENT_TYPES == [
        "on-site",
        "remote",
    ]
    for invalid in (["a", " a "], ["a", " "], ["x" * 65]):
        with pytest.raises(ValidationError):
            Config(EVENT_TYPES=invalid)


def test_endpoint_config_event_types():
    response = req("api/config/event-types", method="get")
    assert response == {"enabled": True, "event_types": EVENT_TYPES}
    req("api/config/event-types", method="get", suppress_auth=True, expected_http_code=401)


def test_event_type_settings_rejected_when_feature_off(monkeypatch):
    from medlogserver.model import event as event_module
    from medlogserver.model.event import EventTypeMode, check_event_type_settings

    monkeypatch.setattr(event_module.config, "EVENT_TYPES", [])
    check_event_type_settings(None, None)
    for mode, event_type in (
        (EventTypeMode.FIXED, ON_SITE),
        (EventTypeMode.DEFAULT, ON_SITE),
        (EventTypeMode.REQUIRED_CHOICE, None),
    ):
        with pytest.raises(ValueError, match="not configured"):
            check_event_type_settings(mode, event_type)


# ---------------------------------------------------------------- event


def test_event_type_settings_validation():
    study_id = _study("TestEventTypeSettingsStudy").study.id

    fixed = _create_event(
        study_id, "fixed", event_type_mode="fixed", event_type=ON_SITE
    )
    dict_must_contain(
        fixed,
        required_keys_and_val={"event_type_mode": "fixed", "event_type": ON_SITE},
    )
    required = _create_event(study_id, "required", event_type_mode="required_choice")
    dict_must_contain(
        required,
        required_keys_and_val={
            "event_type_mode": "required_choice",
            "event_type": None,
        },
    )
    plain = _create_event(study_id, "plain")
    dict_must_contain(
        plain, required_keys_and_val={"event_type_mode": None, "event_type": None}
    )

    # fixed/default need a configured type, required_choice and no mode must not have one
    _create_event(study_id, "e1", 422, event_type_mode="fixed")
    _create_event(study_id, "e2", 422, event_type_mode="default", event_type="unknown")
    _create_event(
        study_id, "e3", 422, event_type_mode="required_choice", event_type=ON_SITE
    )
    _create_event(study_id, "e4", 422, event_type=ON_SITE)
    _create_event(study_id, "e5", 422, event_type_mode="sometimes")

    # PATCH is validated against the merged settings
    event_url = f"api/study/{study_id}/event/{fixed['id']}"
    updated = req(event_url, method="patch", b={"event_type_mode": "default"})
    dict_must_contain(
        updated,
        required_keys_and_val={"event_type_mode": "default", "event_type": ON_SITE},
    )
    req(
        event_url,
        method="patch",
        b={"event_type_mode": "required_choice"},
        expected_http_code=422,
    )
    updated = req(
        event_url,
        method="patch",
        b={"event_type_mode": "required_choice", "event_type": None},
    )
    dict_must_contain(
        updated,
        required_keys_and_val={
            "event_type_mode": "required_choice",
            "event_type": None,
        },
    )
    req(
        f"api/study/{study_id}/event/{plain['id']}",
        method="patch",
        b={"event_type": REMOTE},
        expected_http_code=422,
    )


def test_event_external_id():
    study_id = _study("TestEventExternalIdStudy").study.id

    event = _create_event(study_id, "visit", external_id="  1201 ")
    assert event["external_id"] == "1201"
    listed = req(f"api/study/{study_id}/event", method="get")["items"]
    assert [e["external_id"] for e in listed] == ["1201"]

    event_url = f"api/study/{study_id}/event/{event['id']}"
    assert req(event_url, method="patch", b={"external_id": "V01"})["external_id"] == "V01"
    # an empty value removes the external id
    assert req(event_url, method="patch", b={"external_id": " "})["external_id"] is None
    _create_event(study_id, "too long", 422, external_id="x" * 129)


# ---------------------------------------------------------------- interview


def test_interview_event_type_fixed():
    study = _study("TestInterviewEventTypeFixedStudy")
    study_id, probands = study.study.id, study.proband_ids
    event_id = _create_event(
        study_id, "fixed", event_type_mode="fixed", event_type=ON_SITE
    )["id"]

    interview = _create_interview(study_id, event_id, probands[0])
    assert interview["event_type"] == ON_SITE
    assert (
        _create_interview(study_id, event_id, probands[1], event_type=ON_SITE)[
            "event_type"
        ]
        == ON_SITE
    )
    _create_interview(study_id, event_id, probands[2], 422, event_type=REMOTE)

    _update_interview(
        study_id, event_id, interview["id"], {"event_type": REMOTE}, 422
    )
    updated = _update_interview(
        study_id, event_id, interview["id"], {"proband_has_taken_meds": False}
    )
    assert updated["event_type"] == ON_SITE


def test_interview_event_type_default():
    study = _study("TestInterviewEventTypeDefaultStudy")
    study_id, probands = study.study.id, study.proband_ids
    event_id = _create_event(
        study_id, "default", event_type_mode="default", event_type=ON_SITE
    )["id"]

    interview = _create_interview(study_id, event_id, probands[0])
    assert interview["event_type"] == ON_SITE
    assert (
        _create_interview(study_id, event_id, probands[1], event_type=REMOTE)[
            "event_type"
        ]
        == REMOTE
    )
    _create_interview(study_id, event_id, probands[2], 422, event_type="unknown")

    updated = _update_interview(
        study_id, event_id, interview["id"], {"event_type": PHONE}
    )
    assert updated["event_type"] == PHONE
    # left out or null keeps the stored type
    updated = _update_interview(
        study_id, event_id, interview["id"], {"event_type": None}
    )
    assert updated["event_type"] == PHONE
    _update_interview(
        study_id, event_id, interview["id"], {"event_type": "unknown"}, 422
    )


def test_interview_event_type_required_choice():
    study = _study("TestInterviewEventTypeRequiredStudy")
    study_id, probands = study.study.id, study.proband_ids
    event_id = _create_event(
        study_id, "required", event_type_mode="required_choice"
    )["id"]

    _create_interview(study_id, event_id, probands[0], 422)
    _create_interview(study_id, event_id, probands[0], 422, event_type=None)
    _create_interview(study_id, event_id, probands[0], 422, event_type="unknown")
    interview = _create_interview(study_id, event_id, probands[0], event_type=REMOTE)
    assert interview["event_type"] == REMOTE

    updated = _update_interview(
        study_id, event_id, interview["id"], {"event_type": ON_SITE}
    )
    assert updated["event_type"] == ON_SITE


def test_interview_event_type_not_tracked():
    study = _study("TestInterviewEventTypeNotTrackedStudy")
    study_id, probands = study.study.id, study.proband_ids
    event_id = _create_event(study_id, "plain")["id"]

    interview = _create_interview(study_id, event_id, probands[0])
    assert interview["event_type"] is None
    _create_interview(study_id, event_id, probands[1], 422, event_type=ON_SITE)
    _update_interview(
        study_id, event_id, interview["id"], {"event_type": ON_SITE}, 422
    )


def test_interview_event_type_after_event_settings_change():
    """Interviews created before the event got a mode (e.g. all interviews after the
    migration) get the type on their next update, or have to choose one."""
    study = _study("TestInterviewEventTypeSettingsChangeStudy")
    study_id, probands = study.study.id, study.proband_ids
    event_id = _create_event(study_id, "later typed")["id"]
    event_url = f"api/study/{study_id}/event/{event_id}"
    first = _create_interview(study_id, event_id, probands[0])
    second = _create_interview(study_id, event_id, probands[1])
    assert first["event_type"] is None and second["event_type"] is None

    req(
        event_url,
        method="patch",
        b={"event_type_mode": "fixed", "event_type": REMOTE},
    )
    updated = _update_interview(
        study_id, event_id, first["id"], {"proband_has_taken_meds": False}
    )
    assert updated["event_type"] == REMOTE

    req(
        event_url,
        method="patch",
        b={"event_type_mode": "required_choice", "event_type": None},
    )
    # an interview keeps its type when the event settings change
    updated = _update_interview(
        study_id, event_id, first["id"], {"proband_has_taken_meds": True}
    )
    assert updated["event_type"] == REMOTE
    _update_interview(
        study_id, event_id, second["id"], {"proband_has_taken_meds": False}, 422
    )
    updated = _update_interview(
        study_id, event_id, second["id"], {"event_type": PHONE}
    )
    assert updated["event_type"] == PHONE


# ---------------------------------------------------------------- export


def _export(study_id, format_: str) -> str | Dict:
    """The CSV export as text, the JSON export parsed."""
    export_job = req(
        f"api/study/{study_id}/export", method="post", q={"format": format_}
    )
    finished_job = _wait_for_export(str(study_id), export_job["export_id"])
    dict_must_contain(
        finished_job, required_keys_and_val={"error": None, "state": "success"}
    )
    export = req(finished_job["download_file_path"], method="get")
    return export.decode() if format_ == "csv" else export


def test_export_contains_event_type_and_external_id():
    study_data = create_test_study(
        study_name="TestExportEventTypeStudy",
        with_events=1,
        with_interviews_per_event_per_proband=1,
        with_intakes=1,
        proband_count=1,
    )
    study_id = study_data.study.id
    event_id = study_data.events[0].event.id
    interview_id = study_data.events[0].interviews[0].interview.id
    req(
        f"api/study/{study_id}/event/{event_id}",
        method="patch",
        b={
            "external_id": "1201",
            "event_type_mode": "default",
            "event_type": ON_SITE,
        },
    )
    _update_interview(study_id, event_id, interview_id, {"event_type": REMOTE})

    rows = list(csv.DictReader(io.StringIO(_export(study_id, "csv"))))
    assert len(rows) == 1
    assert rows[0]["event_external_id"] == "1201"
    assert rows[0]["interview_event_type"] == REMOTE
    # the event's own settings are not exported, only the type the interview was
    assert "event_type" not in rows[0]
    assert "event_type_mode" not in rows[0]

    exported = _export(study_id, "json")
    intake = exported["intakes"][0]
    assert intake["event"]["external_id"] == "1201"
    assert intake["interview"]["event_type"] == REMOTE
    assert "event_type" not in intake["event"]
    assert "event_type_mode" not in intake["event"]
