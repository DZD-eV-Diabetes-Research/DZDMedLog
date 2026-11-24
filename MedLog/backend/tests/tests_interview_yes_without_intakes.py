"""Interviews answered "Yes, meds taken" without intakes (issue #409), backend part.

* `PATCH .../interview/{id}` rejects `proband_has_taken_meds = false` while the
  interview has intakes. Without intakes, the answer can be changed in both
  directions, also together with completing the interview.
* The interviewer who created an interview can delete it only while it has no
  intakes and within `INTERVIEW_SELF_DELETE_WINDOW_HOURS` (default 168) hours after
  it was entered (`created_at`). Study admins can always delete it.
* Interview responses carry `self_delete_until_utc`.
"""

import asyncio
import datetime
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from utils import (
    req,
    dictyfy,
    create_test_study,
    create_test_user,
    authorize_for_access_token,
    TestDataContainerStudy,
)
from tests_export_performance import session_db

from medlogserver.config import Config
from medlogserver.model.interview import Interview, interview_self_delete_until
from medlogserver.model.intake import IntakeCreateAPI, ConsumedMedsTodayAnswers

WINDOW_HOURS = Config().INTERVIEW_SELF_DELETE_WINDOW_HOURS


def _study(name: str) -> TestDataContainerStudy:
    return create_test_study(study_name=name, with_events=1, proband_count=1)


def _paths(study: TestDataContainerStudy, interview_id: str):
    study_id = str(study.study.id)
    event_id = str(study.events[0].event.id)
    return (
        f"api/study/{study_id}/event/{event_id}/interview/{interview_id}",
        f"api/study/{study_id}/interview/{interview_id}/intake",
    )


def _create_interview(
    study: TestDataContainerStudy,
    proband_id: str,
    taken_meds: bool = True,
    access_token: str = None,
) -> dict:
    return req(
        f"api/study/{study.study.id}/event/{study.events[0].event.id}/interview",
        method="post",
        b={"proband_external_id": proband_id, "proband_has_taken_meds": taken_meds},
        access_token=access_token,
    )


def _add_intake(intake_path: str, access_token: str = None) -> dict:
    drug = req("/api/drug/search", method="get", q={"search_term": "Test2Drug"})[
        "items"
    ][0]["drug"]
    return req(
        intake_path,
        method="post",
        b=dictyfy(
            IntakeCreateAPI(
                drug_id=drug["id"],
                intake_start_date=datetime.date(2024, 1, 1),
                consumed_meds_today=ConsumedMedsTodayAnswers.NO,
                as_needed_dose_unit=None,
            )
        ),
        access_token=access_token,
    )


def _interviewer(study: TestDataContainerStudy, name: str) -> tuple[str, str]:
    """Create a plain user with interviewer permission on the study. Returns (id, token)."""
    user = create_test_user(name, f"pw_{name}", f"{name}@test.de")
    req(
        f"/api/study/{study.study.id}/permissions/{user.id}",
        method="put",
        b={"is_study_interviewer": True, "is_study_admin": False},
    )
    return str(user.id), authorize_for_access_token(name, f"pw_{name}")


def _set_created_at(session_db, interview_id: str, hours_ago: float):
    """Pretend the interview was entered `hours_ago` hours ago."""

    async def update():
        async with AsyncSession(session_db.engine) as session:
            interview = await session.get(Interview, uuid.UUID(interview_id))
            interview.created_at = datetime.datetime.now(
                tz=datetime.timezone.utc
            ).replace(tzinfo=None) - datetime.timedelta(hours=hours_ago)
            session.add(interview)
            await session.commit()

    asyncio.run(update())


# ---------------------------------------------------------------------------
# PATCH proband_has_taken_meds
# ---------------------------------------------------------------------------


def test_patch_to_no_meds_is_rejected_while_interview_has_intakes():
    study = _study("TestIssue409PatchNoWithIntakes")
    interview = _create_interview(study, "P409PATCH1")
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path)

    req(
        interview_path,
        method="patch",
        b={"proband_has_taken_meds": False},
        expected_http_code=409,
    )
    # also when sent together with completing the interview
    req(
        interview_path,
        method="patch",
        b={
            "proband_has_taken_meds": False,
            "interview_end_time_utc": datetime.datetime.now().isoformat(),
        },
        expected_http_code=409,
    )
    stored = req(interview_path, method="get")
    assert stored["proband_has_taken_meds"] is True
    assert stored["interview_end_time_utc"] is None

    # Other updates of an interview with intakes keep working
    req(interview_path, method="patch", b={"proband_has_taken_meds": True})
    completed = req(
        interview_path,
        method="patch",
        b={"interview_end_time_utc": datetime.datetime.now().isoformat()},
    )
    assert completed["interview_end_time_utc"] is not None


def test_patch_no_meds_answer_can_be_changed_without_intakes():
    study = _study("TestIssue409PatchNoWithoutIntakes")
    interview = _create_interview(study, "P409PATCH2")
    interview_path, _ = _paths(study, interview["id"])

    # "Abschließen und auf Nein ändern": one PATCH that completes and switches to "No"
    end_time = datetime.datetime(2025, 3, 1, 10, 0).isoformat()
    updated = req(
        interview_path,
        method="patch",
        b={"proband_has_taken_meds": False, "interview_end_time_utc": end_time},
    )
    assert updated["proband_has_taken_meds"] is False
    assert updated["interview_end_time_utc"] == end_time

    # and back to "Yes"
    updated = req(interview_path, method="patch", b={"proband_has_taken_meds": True})
    assert updated["proband_has_taken_meds"] is True


def test_patch_without_meds_field_does_not_check_intakes():
    study = _study("TestIssue409PatchOtherField")
    interview = _create_interview(study, "P409PATCH3")
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path)
    req(
        interview_path,
        method="patch",
        b={"interview_start_time_utc": datetime.datetime(2025, 1, 1).isoformat()},
        expected_http_code=200,
    )


# ---------------------------------------------------------------------------
# self_delete_until_utc
# ---------------------------------------------------------------------------


def test_interview_responses_contain_self_delete_until():
    study = _study("TestIssue409SelfDeleteUntil")
    interview = _create_interview(study, "P409UNTIL")
    interview_path, _ = _paths(study, interview["id"])

    expected = (
        datetime.datetime.fromisoformat(interview["created_at"])
        + datetime.timedelta(hours=WINDOW_HOURS)
    ).isoformat()
    assert interview["self_delete_until_utc"] == expected
    assert req(interview_path, method="get")["self_delete_until_utc"] == expected
    listed = req(
        f"api/study/{study.study.id}/event/{study.events[0].event.id}/interview",
        method="get",
    )
    assert [i["self_delete_until_utc"] for i in listed] == [expected]
    current = req(
        f"api/study/{study.study.id}/proband/P409UNTIL/interview/current", method="get"
    )
    assert current["self_delete_until_utc"] == expected


def test_self_delete_until_with_short_and_zero_window(monkeypatch):
    from medlogserver.model import interview as interview_module

    created_at = datetime.datetime(2025, 5, 1, 12, 0)
    monkeypatch.setattr(interview_module.config, "INTERVIEW_SELF_DELETE_WINDOW_HOURS", 2)
    assert interview_self_delete_until(created_at) == datetime.datetime(2025, 5, 1, 14, 0)
    monkeypatch.setattr(interview_module.config, "INTERVIEW_SELF_DELETE_WINDOW_HOURS", 0)
    assert interview_self_delete_until(created_at) == created_at


def test_config_rejects_negative_window(monkeypatch):
    import pydantic
    import pytest

    monkeypatch.setenv("INTERVIEW_SELF_DELETE_WINDOW_HOURS", "-1")
    with pytest.raises(pydantic.ValidationError):
        Config()


# ---------------------------------------------------------------------------
# DELETE by the creating interviewer
# ---------------------------------------------------------------------------


def test_owner_can_delete_own_interview_within_window(session_db):
    study = _study("TestIssue409OwnerDeleteInWindow")
    _, token = _interviewer(study, "i409_owner_in_window")
    interview = _create_interview(study, "P409DEL1", access_token=token)
    interview_path, _ = _paths(study, interview["id"])
    # entered long after the interview date: the window counts from created_at
    req(
        interview_path,
        method="patch",
        b={"interview_start_time_utc": datetime.datetime(2020, 1, 1).isoformat()},
        access_token=token,
    )
    _set_created_at(session_db, interview["id"], hours_ago=WINDOW_HOURS - 0.5)

    req(interview_path, method="delete", expected_http_code=204, access_token=token)
    req(interview_path, method="get", expected_http_code=404)


def test_owner_cannot_delete_own_interview_after_window(session_db):
    study = _study("TestIssue409OwnerDeleteAfterWindow")
    _, token = _interviewer(study, "i409_owner_after_window")
    interview = _create_interview(study, "P409DEL2", access_token=token)
    interview_path, _ = _paths(study, interview["id"])
    _set_created_at(session_db, interview["id"], hours_ago=WINDOW_HOURS + 0.5)

    response = req(
        interview_path, method="delete", expected_http_code=403, access_token=token
    )
    assert "study admin" in response["detail"]
    assert req(interview_path, method="get")["id"] == interview["id"]

    # a study admin still can
    req(interview_path, method="delete", expected_http_code=204)


def test_owner_cannot_delete_own_interview_with_intakes():
    study = _study("TestIssue409OwnerDeleteWithIntakes")
    _, token = _interviewer(study, "i409_owner_with_intakes")
    interview = _create_interview(study, "P409DEL3", access_token=token)
    interview_path, intake_path = _paths(study, interview["id"])
    intake = _add_intake(intake_path, access_token=token)

    req(interview_path, method="delete", expected_http_code=409, access_token=token)
    assert req(interview_path, method="get")["id"] == interview["id"]

    # after deleting the intake, the owner can delete the interview
    req(
        f"api/study/{study.study.id}/interview/{interview['id']}/intake/{intake['id']}",
        method="delete",
        expected_http_code=200,
        access_token=token,
    )
    req(interview_path, method="delete", expected_http_code=204, access_token=token)


def test_other_interviewer_cannot_delete_interview_in_window():
    study = _study("TestIssue409OtherInterviewerDelete")
    _, owner_token = _interviewer(study, "i409_owner_other")
    _, other_token = _interviewer(study, "i409_other")
    interview = _create_interview(study, "P409DEL4", access_token=owner_token)
    interview_path, _ = _paths(study, interview["id"])
    req(
        interview_path,
        method="delete",
        expected_http_code=403,
        access_token=other_token,
    )


def test_global_admin_can_delete_old_interview_with_intakes(session_db):
    study = _study("TestIssue409AdminDelete")
    _, token = _interviewer(study, "i409_owner_admin_case")
    interview = _create_interview(study, "P409DEL5", access_token=token)
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path, access_token=token)
    _set_created_at(session_db, interview["id"], hours_ago=WINDOW_HOURS * 10)

    req(interview_path, method="delete", expected_http_code=204)
    intakes = req(
        f"api/study/{study.study.id}/proband/P409DEL5/intake",
        method="get",
        q={"interview_id": interview["id"]},
    )
    assert intakes["count"] == 0


def test_delete_with_wrong_event_is_rejected():
    study = create_test_study(
        study_name="TestIssue409DeleteWrongEvent", with_events=2, proband_count=1
    )
    interview = _create_interview(study, "P409DEL6")
    other_event_id = study.events[1].event.id
    req(
        f"api/study/{study.study.id}/event/{other_event_id}/interview/{interview['id']}",
        method="delete",
        expected_http_code=404,
    )
    interview_path, _ = _paths(study, interview["id"])
    assert req(interview_path, method="get")["id"] == interview["id"]


def _set_taken_meds_in_db(session_db, interview_id: str, value: bool):
    """Write the flag directly, like data from before issue #404."""

    async def update():
        async with AsyncSession(session_db.engine) as session:
            interview = await session.get(Interview, uuid.UUID(interview_id))
            interview.proband_has_taken_meds = value
            session.add(interview)
            await session.commit()

    asyncio.run(update())


def test_patch_keeps_working_for_legacy_no_meds_interview_with_intakes(session_db):
    study = _study("TestIssue409PatchLegacyNoWithIntakes")
    interview = _create_interview(study, "P409LEGACY")
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path)
    _set_taken_meds_in_db(session_db, interview["id"], False)

    # a form that sends the unchanged value along with another field
    end_time = datetime.datetime(2025, 3, 1, 10, 0).isoformat()
    updated = req(
        interview_path,
        method="patch",
        b={"proband_has_taken_meds": False, "interview_end_time_utc": end_time},
    )
    assert updated["interview_end_time_utc"] == end_time
    assert updated["proband_has_taken_meds"] is False


def test_owner_after_window_with_intakes_gets_window_error(session_db):
    """Past the window, the owner must not be told to delete the intakes first."""
    study = _study("TestIssue409OwnerAfterWindowWithIntakes")
    _, token = _interviewer(study, "i409_owner_after_window_intakes")
    interview = _create_interview(study, "P409DEL7", access_token=token)
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path, access_token=token)
    _set_created_at(session_db, interview["id"], hours_ago=WINDOW_HOURS + 0.5)

    req(interview_path, method="delete", expected_http_code=403, access_token=token)


def test_plain_study_admin_can_delete_old_interview_with_intakes(session_db):
    """A study admin without global admin role is not bound by the self-delete rules."""
    study = _study("TestIssue409PlainStudyAdminDelete")
    _, owner_token = _interviewer(study, "i409_owner_plain_admin_case")
    admin = create_test_user(
        "i409_plain_study_admin", "pw_i409_plain_study_admin", "i409_psa@test.de"
    )
    req(
        f"/api/study/{study.study.id}/permissions/{admin.id}",
        method="put",
        b={"is_study_interviewer": False, "is_study_admin": True},
    )
    admin_token = authorize_for_access_token(
        "i409_plain_study_admin", "pw_i409_plain_study_admin"
    )
    interview = _create_interview(study, "P409DEL8", access_token=owner_token)
    interview_path, intake_path = _paths(study, interview["id"])
    _add_intake(intake_path, access_token=owner_token)
    _set_created_at(session_db, interview["id"], hours_ago=WINDOW_HOURS * 10)

    req(
        interview_path, method="delete", expected_http_code=204, access_token=admin_token
    )
