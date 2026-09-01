from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn, Type

from fastapi import (
    Depends,
    Security,
    APIRouter,
    HTTPException,
    status,
    Body,
    Path,
    Query,
)
import uuid
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from medlogserver.db.interview import InterviewCRUD
from medlogserver.db.user import User
from medlogserver.api.auth.security import get_current_user
from medlogserver.api.base import HTTPErrorResponeRepresentation
from medlogserver.model.intake import (
    Intake,
    IntakeCreate,
    IntakeUpdate,
    IntakeCreateAPI,
    IntakeDetailListItem,
    IntakeValidationError,
)
from medlogserver.db.intake import IntakeCRUD
from medlogserver.api.study_access import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    assert_interview_is_part_of_study,
    assert_intake_is_part_of_study,
)
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_intake_router: APIRouter = APIRouter()


def _intake_validation_error_detail(
    exception: IntakeValidationError | ValidationError,
) -> dict | str:
    """Build the 422 body for a rejected intake.

    Violations of the plausibility rules carry the rule that broke, the fields it
    concerns and the date the check was made against, so the frontend can put the
    hint on the right input and build its own translated message instead of
    falling back to the English `msg`. The older field-presence and mutual
    exclusivity errors are raised inside pydantic validators, get wrapped in a
    `ValidationError` and keep their plain string detail.
    """
    rule_id = getattr(exception, "rule_id", None)
    if rule_id is None:
        return str(exception)
    return {
        "rule": rule_id,
        "fields": list(getattr(exception, "fields", ())),
        "msg": str(exception),
        "reference": getattr(exception, "reference", None),
        "reference_date": getattr(exception, "reference_date", None),
        "context": dict(getattr(exception, "context", {})),
    }


INTAKE_422_RESPONSE_DOC = {
    "description": (
        "**UNPROCESSABLE ENTITY** — Returned when the request body violates one of the following validation rules:\n\n"
        "**Start Date (exactly one required)**\n"
        "- Both `intake_start_date` and `intake_start_date_option` are set — only one may be provided.\n"
        "- Neither `intake_start_date` nor `intake_start_date_option` is set — exactly one must be provided.\n\n"
        "**End Date (at most one allowed)**\n"
        "- Both `intake_end_date` and `intake_end_date_option` are set — only one may be provided. "
        "If neither is sent, `intake_end_date_option` defaults to `ONGOING`.\n\n"
        "**Intake Mode (mutually exclusive dose fields)**\n"
        "- `intake_regular_or_as_needed` is `REGULAR` but `as_needed_dose_unit` is not `null`.\n"
        "- `intake_regular_or_as_needed` is `AS_NEEDED` but `regular_intervall_of_daily_dose` is not `null`.\n\n"
        "**Plausibility (combinations that cannot be true)**\n"
        "Two reference dates are used. The \"not in the future\" rules compare against the "
        "server's current UTC date, without tolerance: tomorrow is a future date. The "
        "\"taken today\" rules compare against the day the parent interview was started, "
        "because that is the day the proband answered the question. That keeps an interview "
        "that stays open across midnight, a retroactively entered interview and a later "
        "correction of an entry from turning a correct answer into a contradiction. Those "
        "comparisons get one day of tolerance in both directions, to absorb the offset between "
        "the stored UTC timestamp and the interviewer's local time.\n"
        "The rules are checked on the record as it will be stored, so a PATCH is validated "
        "against the merged record, not just the payload. A PATCH only triggers the rules that "
        "concern a field it actually sends.\n"
        "- `end_date_before_start_date` — `intake_end_date` is before `intake_start_date`. "
        "The same day for both is allowed.\n"
        "- `start_date_in_future` — `intake_start_date` lies after the current date.\n"
        "- `end_date_in_future` — `intake_end_date` lies after the current date.\n"
        "- `consumed_today_with_past_end_date` — `consumed_meds_today` is `Yes` while "
        "`intake_end_date` lies before the interview date.\n"
        "- `consumed_today_with_future_start_date` — `consumed_meds_today` is `Yes` while "
        "`intake_start_date` lies after the interview date.\n"
        "- `dose_per_day_negative` — `dose_per_day` is negative. `0` is allowed and means the "
        "daily dose is unknown.\n"
        "- `as_needed_dose_unit_negative` — `as_needed_dose_unit` is negative. `0` is allowed "
        "and means the dose is unknown.\n"
        "- `start_date_implausibly_old` / `end_date_implausibly_old` — the date is before 1900-01-01.\n\n"
        "Rules that need an exact date are skipped when `intake_start_date_option` / "
        "`intake_end_date_option` is set instead of a date, because the option carries no date to "
        "compare. `consumed_meds_today` of `No` or `UNKNOWN` never conflicts with a date.\n\n"
        "A plausibility violation returns an object as `detail`, carrying the `rule` that broke "
        "and the `fields` it concerns. For a translated, client-side message it also carries "
        "`reference_date`, the ISO date the broken rule compared against (`null` for a rule that "
        "compares no date), and `reference`, naming which date that is: `today`, "
        "`interview_date` or `earliest_plausible_date`. `context` holds all three dates, for a "
        "message that needs more than the one the rule used. The other rules above return a "
        "plain string."
    ),
    "content": {
        "application/json": {
            "examples": {
                "field_presence": {
                    "summary": "Mutually exclusive fields",
                    "value": {
                        "detail": "Only one of 'intake_start_date' or 'intake_start_date_option' may be set."
                    },
                },
                "plausibility": {
                    "summary": "Plausibility rule violated",
                    "value": {
                        "detail": {
                            "rule": "consumed_today_with_past_end_date",
                            "fields": ["consumed_meds_today", "intake_end_date"],
                            "msg": (
                                "'consumed_meds_today' is 'Yes', but 'intake_end_date' is before "
                                "2026-06-15, the day this interview was started. 'Today' refers to "
                                "the day of the interview, and an intake that had already ended "
                                "cannot have been taken on that day."
                            ),
                            "reference": "interview_date",
                            "reference_date": "2026-06-15",
                            "context": {
                                "today": "2026-06-20",
                                "interview_date": "2026-06-15",
                                "earliest_plausible_date": "1900-01-01",
                            },
                        }
                    },
                },
            }
        }
    },
}


IntakeQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Intake, default_order_by_attr="created_at"
)


############
@fast_api_intake_router.get(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description=f"Get a certain intake record by it id",
)
async def get_intake(
    intake_id: uuid.UUID,
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> Intake:
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    return await intake_crud.get(
        id_=intake_id,
        study_id=study_access.study.id,
        raise_exception_if_none=HTTPException(status_code=status.HTTP_404_NOT_FOUND),
    )


############
@fast_api_intake_router.post(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=Intake,
    description="""Create intake record in certain interview. user must have at least 'interviewer'-permissions on study.
    **Start Date** — exactly one of `intake_start_date` or `intake_start_date_option` must be set.  
    Sending both returns 400. The omitted field is automatically nulled out.  
    **End Date** — at most one of `intake_end_date` or `intake_end_date_option` may be set.  
    Sending both returns 400. If neither is provided, `intake_end_date_option` defaults to `ONGOING`.
    The omitted field is automatically nulled out.  
    **Intake mode** — mutually exclusive fields depending on `intake_regular_or_as_needed`:  
    - `REGULAR`: `as_needed_dose_unit` must be `null`  
    - `AS_NEEDED`: `regular_intervall_of_daily_dose` must be `null`  
    """,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: INTAKE_422_RESPONSE_DOC},
)
async def create_intake(
    intake: Annotated[IntakeCreateAPI, Body()],
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Intake:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of the study. otherwise caller could evade study permissions here by calling a interview id from another study.
    await assert_interview_is_part_of_study(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    log.debug(f"create_intake(): intake: {intake}")
    log.debug(f"interview_id: {interview_id}")
    # ToDo: Casting to uuid is a hotfix here. it should be validated/transformed in the model itself
    # interview_id = uuid.UUID(interview_id)
    try:
        intake_create = IntakeCreate(interview_id=interview_id, **intake.model_dump())
        return await intake_crud.create(intake_create)
    except (IntakeValidationError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_intake_validation_error_detail(e),
        )


############
@fast_api_intake_router.patch(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description="""Update intake record. user must have at least 'interviewer'-permissions on study.  
    **Start Date** — exactly one of `intake_start_date` or `intake_start_date_option` must be set.  
    Sending both returns 400. The omitted field is automatically nulled out.  
    **End Date** — at most one of `intake_end_date` or `intake_end_date_option` may be set.  
    Sending both returns 400. If neither is provided, `intake_end_date_option` defaults to `ONGOING`.
    The omitted field is automatically nulled out.  
    **Intake mode** — mutually exclusive fields depending on `intake_regular_or_as_needed`:  
    - `REGULAR`: `as_needed_dose_unit` must be `null`  
    - `AS_NEEDED`: `regular_intervall_of_daily_dose` must be `null`  
    """,
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: INTAKE_422_RESPONSE_DOC},
)
async def update_intake(
    intake_id: uuid.UUID,
    intake: IntakeUpdate,
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> Intake:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    try:
        return await intake_crud.update(update_obj=intake, id_=intake_id)
    except (IntakeValidationError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=_intake_validation_error_detail(e),
        )


############
@fast_api_intake_router.delete(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    summary="Delete an intake record",
    responses={
        status.HTTP_200_OK: {"description": "Intake deleted successfully."},
        status.HTTP_401_UNAUTHORIZED: {
            "model": HTTPErrorResponeRepresentation,
            "description": "Not authenticated.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPErrorResponeRepresentation,
            "description": (
                "Caller has no interviewer-level access on this study, or "
                "is an interviewer but did not create the parent interview. "
                "Ownership is determined by the parent interview's `interviewer_user_id`, "
                "not by who added this intake. Only the interview owner or a study/global admin may delete it."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPErrorResponeRepresentation,
            "description": "No intake or interview with the given IDs exists within this study.",
        },
    },
)
async def delete_intake(
    intake_id: Annotated[uuid.UUID, Path(description="ID of the intake record to delete.")],
    interview_id: Annotated[uuid.UUID, Path(description="ID of the interview the intake belongs to.")],
    current_user: Annotated[User, Security(get_current_user)],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
):
    """
    Delete a single medication intake record.

    **Authorization:** caller must have at least interviewer role (`403` otherwise), and must be
    either the interviewer who created the **parent interview** or a study/global admin (`403` otherwise).
    Ownership is tied to the interview, not to who added this specific intake.

    To delete all intakes of an interview at once, delete the interview itself
    (`DELETE /study/{study_id}/event/{event_id}/interview/{interview_id}`).
    """
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete intake",
        )
    # Verify the intake belongs to the given interview and study to prevent cross-study access.
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    interview = await interview_crud.get(
        interview_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No interview with id '{interview_id}'",
        ),
    )
    is_owner = interview.interviewer_user_id == current_user.id
    if not (study_access.user_is_study_admin() or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this intake. Must be study admin or the interviewer who created the parent interview.",
        )
    log.warning("ToDo: The med record are not deleted yet")
    return await intake_crud.delete(intake_id)


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/intake",
    response_model=PaginatedResponse[Intake],
    description=f"List all medicine intakes of one proband.",
)
async def list_all_intakes(
    proband_id: str,
    interview_id: Annotated[
        uuid.UUID, Query(description="Filter intakes by a certain interview.")
    ] = None,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(IntakeQueryParams),
) -> PaginatedResponse[Intake]:
    intakes = await intake_crud.list(
        filter_study_id=study_access.study.id,
        filter_proband_external_id=proband_id,
        filter_interview_id=interview_id,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await intake_crud.count(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=interview_id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        ),
        offset=pagination.offset,
        count=len(intakes),
        items=intakes,
    )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/intake/details",
    response_model=PaginatedResponse[IntakeDetailListItem],
    description=f"List all medicine intakes of one proband, but as detailed table that includes Event, Interview and Drug details.",
)
async def list_all_intakes_detailed(
    proband_id: str,
    interview_id: Annotated[
        uuid.UUID, Query(description="Filter intakes by a certain interview.")
    ] = None,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(IntakeQueryParams),
) -> PaginatedResponse[IntakeDetailListItem]:
    intakes = await intake_crud.list_detailed(
        filter_study_id=study_access.study.id,
        filter_proband_external_id=proband_id,
        filter_interview_id=interview_id,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await intake_crud.count(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=interview_id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        ),
        offset=pagination.offset,
        count=len(intakes),
        items=intakes,
    )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands last completed interview.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "No interview exists yet.",
            "headers": {
                "X-Reason": {
                    "description": "Reason why no content was returned",
                    "schema": {"type": "string", "example": "No interview exist yet"},
                }
            },
        }
    },
)
async def list_all_intakes_of_last_completed_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    last_completed_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id,
        proband_external_id=proband_id,
        completed=True,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
    )
    if last_completed_interview:
        return await intake_crud.list(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_completed_interview.id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        )
    else:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last/intake/details",
    response_model=List[IntakeDetailListItem],
    description=f"List all medicine intakes of one probands last completed interview with all drug details attached.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "No interview exists yet.",
            "headers": {
                "X-Reason": {
                    "description": "Reason why no content was returned",
                    "schema": {"type": "string", "example": "No interview exist yet"},
                }
            },
        }
    },
)
async def list_all_intakes_of_last_completed_interview_detailed(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[IntakeDetailListItem]:
    last_completed_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id,
        proband_external_id=proband_id,
        completed=True,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
    )
    if last_completed_interview:
        return await intake_crud.list_detailed(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_completed_interview.id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        )
    else:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )


############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands current (non completed / Interview.interview_end_time_utc is None) interview.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "No interview exists yet.",
            "headers": {
                "X-Reason": {
                    "description": "Reason why no content was returned",
                    "schema": {"type": "string", "example": "No interview exist yet"},
                }
            },
        }
    },
)
async def list_all_intakes_of_last_uncompleted_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake] | Response:
    last_uncompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id,
        proband_external_id=proband_id,
        completed=False,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
    )
    if last_uncompleted_interview:
        return await intake_crud.list(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_uncompleted_interview.id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        )
    else:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake/details",
    response_model=List[IntakeDetailListItem],
    description=f"List all medicine intakes of one probands last completed interview with all details attached.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "No interview exists yet.",
            "headers": {
                "X-Reason": {
                    "description": "Reason why no content was returned",
                    "schema": {"type": "string", "example": "No interview exist yet"},
                }
            },
        }
    },
)
async def list_all_intakes_of_last_uncompleted_interview_detailed(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> IntakeDetailListItem:
    last_incompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id,
        proband_external_id=proband_id,
        completed=False,
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
    )
    if last_incompleted_interview:
        return await intake_crud.list_detailed(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_incompleted_interview.id,
            proband_external_id_normalization=study_access.study.proband_external_id_normalization,
        )
    else:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )


############
@fast_api_intake_router.get(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of interview.",
)
async def list_all_intakes_of_interview(
    interview_id: uuid.UUID,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    return await intake_crud.list(
        filter_interview_id=interview_id, filter_study_id=study_access.study.id
    )
