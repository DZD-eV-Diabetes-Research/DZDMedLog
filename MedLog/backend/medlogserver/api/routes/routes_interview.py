from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn

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


from medlogserver.config import Config
from medlogserver.model.interview import (
    Interview,
    InterviewCreate,
    InterviewUpdate,
)
from medlogserver.db.interview import InterviewCRUD
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
    event_id: Annotated[str, Path()],
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
    event_id: Annotated[str, Path()],
    interview_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    interview = await interview_crud.get(interview_id=interview_id)
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
    response_model=Interview,
    description=f"Get the last completed interview of proband.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "There is no completed interview yet",
        }
    },
)
async def get_last_completed_interview(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=True
    )
    if interview is None:
        # https://fastapi.tiangolo.com/advanced/additional-responses/#additional-response-with-model
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=HTTPMessage("No interview completed yet").model_dump(),
        )
    return interview


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current",
    response_model=Interview,
    description=f"Get the latest non completed interview of proband.",
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "There is no completed interview yet",
        }
    },
)
async def get_last_non_completed_interview(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Interview]:
    interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if interview is None:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
        )
    return interview


@fast_api_interview_router.post(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=List[Interview],
    description=f"Create new interview",
)
async def create_interview(
    interview: Annotated[InterviewCreate, Body()],
    event_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> User:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
        )
    return await interview_crud.create(interview)


@fast_api_interview_router.patch(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    response_model=Interview,
    description=f"Update existing interview",
)
async def update_interview(
    interview_id: str,
    event_id: str,
    interview_update: InterviewUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> User:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
        )
    interview_from_db = await interview_crud.get(interview_id)
    if interview_from_db is None or interview_from_db.event_id != event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview with this id under this event available",
        )
    return await interview_crud.update(interview_id, interview_update)


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
    interview_id: str,
    event_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> None:
    if not study_access.user_has_interviewer_permission():
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
