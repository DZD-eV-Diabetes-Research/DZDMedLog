from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List

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


from fastapi import Depends, APIRouter


from medlogserver.db.user.crud import User


from medlogserver.db.event.model import Event, EventUpdate
from medlogserver.db.event.crud import EventCRUD


from medlogserver.config import Config
from medlogserver.api.routes_app.security import (
    user_has_study_access,
    UserStudyAccess,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_event_router: APIRouter = APIRouter()


@fast_api_event_router.get(
    "/study/{study_id}/event",
    response_model=List[Event],
    description=f"List all studies the user has access too.",
)
async def list_events(
    hide_completed: bool = Query(False),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> List[Event]:
    return await event_crud.list(
        filter_by_study_id=study_access.study.id, hide_completed=hide_completed
    )


@fast_api_event_router.post(
    "/study/{study_id}/event",
    response_model=Event,
    description=f"Create a new event.",
)
async def create_event(
    event: Event,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> Event:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to create new event",
        )
    return await event_crud.create(
        event,
        raise_custom_exception_if_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event with name '{event.name}' allready exists",
        ),
    )


@fast_api_event_router.patch(
    "/study/{study_id}/event/{event_id}",
    response_model=Event,
    description=f"Update existing event",
)
async def update_event(
    event_id: str,
    event: EventUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> Event:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to update event",
        )
    return await event_crud.update(
        event_id=event_id,
        event=event,
        raise_exception_if_not_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No study with id '{event_id}'",
        ),
    )


@fast_api_event_router.delete(
    "/study/{study_id}/event/{event_id}",
    description=f"Delete existing event - Not Yet Implented",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": None},
    },
)
async def delete_event(
    event_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
):
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
