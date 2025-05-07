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
from medlogserver.model.event import Event
from medlogserver.db.event import EventCRUD
from medlogserver.api.study_access import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    UserStudyAccessCollection,
)
from medlogserver.api.base import HTTPMessage

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
    return await interview_crud.list(filter_proband_external_id=proband_id)


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last",
    response_model=Optional[Interview],
    description=f"Get the last completed interview of proband.",
    responses={status.HTTP_204_NO_CONTENT: {"description": "No interview exist yet"}},
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
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )
    return interview


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current",
    response_model=Optional[Interview],
    description=f"Get the latest non completed interview of proband.",
    responses={status.HTTP_204_NO_CONTENT: {"description": "No interview exist yet"}},
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
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )

    return interview


@fast_api_interview_router.post(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=Interview,
    description=f"Create new interview",
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
        )
    event: Event = await event_crud.get(
        event_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No event found with id '{event_id}'",
        ),
    )
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
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
    description=f"Delete existing interview - Not Yet Implented",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": None},
    },
)
async def delete_interview(
    interview_id: uuid.UUID,
    event_id: uuid.UUID,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> None:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to update event",
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deleting a event is not implented",
    )
    # not implemented. Do we need that?
    # That would be a whole process -> delete interviews, intakes. More something for a background task.
    # "a mark for deletion" property and a grace period of one day. or an validation by email  would make sense to prevent accidentaly deletion.
    # or a disable option
    return await event_crud.delete(
        event_id=event_id,
        raise_exception_if_not_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No event with id '{event_id}'",
        ),
    )
