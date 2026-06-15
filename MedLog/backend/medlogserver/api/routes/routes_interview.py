from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn, Optional
import uuid
from fastapi import (
    Depends,
    Security,
    HTTPException,
    status,
    Query,
    Body,
    Form,
    Path,
    Response,
)

from fastapi.responses import JSONResponse

from fastapi import Depends, APIRouter


from medlogserver.db.user import User
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)

from medlogserver.config import Config
from medlogserver.model.interview import (
    Interview,
    InterviewCreate,
    InterviewUpdate,
    InterviewUpdateAPI,
    InterviewCreateAPI,
)

from medlogserver.db.interview import InterviewCRUD
from medlogserver.db.intake import IntakeCRUD
from medlogserver.model.event import Event
from medlogserver.db.event import EventCRUD
from medlogserver.api.study_access import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    UserStudyAccessCollection,
)
from medlogserver.api.base import HTTPMessage, HTTPErrorResponeRepresentation

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_interview_router: APIRouter = APIRouter()


@fast_api_interview_router.get(
    "/study/{study_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of one study.",
)
async def list_all_interviews_of_study(
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    return await interview_crud.list(filter_study_id=study_access.study.id)


@fast_api_interview_router.get(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of an event.",
)
async def list_interviews_by_study_event(
    event_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    return await interview_crud.list(filter_event_id=event_id)


@fast_api_interview_router.get(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    response_model=Interview,
    description=f"Get a certain interview by its id.",
)
async def get_interview(
    event_id: Annotated[uuid.UUID, Path()],
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Interview:
    interview: Interview = await interview_crud.get(interview_id)
    log.debug((interview.event_id, event_id, interview.event_id == event_id))
    if interview.event_id == event_id:
        return interview
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview with this id under this event available",
        )


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of one proband.",
)
async def list_interviews_of_proband(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    return await interview_crud.list(
        filter_proband_external_id=proband_id, filter_study_id=study_access.study.id
    )


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last",
    response_model=Optional[Interview],
    description=f"Get the last completed interview of proband.",
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
async def get_last_completed_interview(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Optional[Interview]:
    interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=True
    )
    if interview is None:
        # https://fastapi.tiangolo.com/advanced/additional-responses/#additional-response-with-model
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )
    return interview


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current",
    response_model=Optional[Interview],
    description=f"Get the latest non completed interview of proband.",
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
async def get_last_non_completed_interview(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Optional[Interview]:
    interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if interview is None:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason": "No interview exist yet"},
        )

    return interview


@fast_api_interview_router.post(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=Interview,
    description=f"Create new interview. At the moment there is artificial restriction that only allows for one interview per proband per event. See https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/127 and https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/130",
)
async def create_interview(
    interview: Annotated[InterviewCreateAPI, Body()],
    event_id: Annotated[uuid.UUID, Path()],
    user: Annotated[User, Security(get_current_user)],
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Interview:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to create interview in this study",
        )
    event: Event = await event_crud.get(
        event_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No event found with id '{event_id}'",
        ),
    )

    # https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/127
    # We want to prevent having more than one interview per event for now as the webclient does not support it
    # this can be removed once https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/130 is closed
    existing_interview = await interview_crud.list(
        filter_event_id=event_id,
        filter_proband_external_id=interview.proband_external_id,
    )
    if len(existing_interview) != 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only one interview per event per proband allowed at the moment. See https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/127",
        )
    # /127

    interview_create = InterviewCreate(
        event_id=event.id,
        interviewer_user_id=user.id,
        **interview.model_dump(exclude_unset=True),
    )
    # create_interview_.event_id = event_id
    return await interview_crud.create(interview_create)


@fast_api_interview_router.patch(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    response_model=Interview,
    description=f"Update existing interview",
)
async def update_interview(
    interview_id: uuid.UUID,
    event_id: uuid.UUID,
    interview_update: InterviewUpdateAPI,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> User:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not authorized to update interview in this study",
        )
    interview_from_db: Interview = await interview_crud.get(interview_id)
    if interview_from_db is None or interview_from_db.event_id != event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview with this id under this event available",
        )
    return await interview_crud.update(update_obj=interview_update, id_=interview_id)


@fast_api_interview_router.delete(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    summary="Delete an interview",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Interview and all its intakes deleted successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": HTTPErrorResponeRepresentation,
            "description": "Not authenticated.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPErrorResponeRepresentation,
            "description": (
                "Caller has no interviewer-level access on this study, or "
                "is an interviewer but did not create this interview. "
                "Only the creating interviewer or a study/global admin may delete it."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPErrorResponeRepresentation,
            "description": "No interview with the given `interview_id` exists within this study and event.",
        },
    },
)
async def delete_interview(
    interview_id: Annotated[uuid.UUID, Path(description="ID of the interview to delete.")],
    event_id: Annotated[uuid.UUID, Path(description="ID of the event the interview belongs to.")],
    current_user: Annotated[User, Security(get_current_user)],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> None:
    """
    Delete an interview and **all its intake records** (cascade delete).

    All intakes belonging to this interview are removed automatically — no need to delete them first.

    **Authorization:** caller must have at least interviewer role (`403` otherwise), and must be
    either the interviewer who created this interview or a study/global admin (`403` otherwise).

    Deleting an interview does not delete the parent event.
    """
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete interview",
        )
    await interview_crud.assert_belongs_to_study(
        interview_id=interview_id,
        study_id=study_access.study.id,
        raise_exception_if_not=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No interview with id '{interview_id}' found in this study",
        ),
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
            detail="Not authorized to delete this interview. Must be study admin or the interviewer who created it.",
        )
    await intake_crud.delete_by_interview_id(interview_id)
    await interview_crud.delete(
        id_=interview_id,
        raise_exception_if_not_exists=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No interview with id '{interview_id}'",
        ),
    )
