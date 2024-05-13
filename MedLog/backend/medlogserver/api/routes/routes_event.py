from typing import Annotated, Sequence, List, Type
from datetime import datetime, timedelta, timezone


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


from medlogserver.db.user import User


from medlogserver.model.event import Event, EventUpdate, EventCreate, EventCreateAPI
from medlogserver.db.event import EventCRUD


from medlogserver.config import Config
from medlogserver.api.study_access import (
    user_has_study_access,
    UserStudyAccess,
)
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_event_router: APIRouter = APIRouter()

EventQueryParams: Type[QueryParamsInterface] = create_query_params_class(Event)


@fast_api_event_router.get(
    "/study/{study_id}/event",
    response_model=PaginatedResponse[Event],
    description=f"List all studies the user has access too.",
)
async def list_events(
    hide_completed: bool = Query(False),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(EventQueryParams),
) -> PaginatedResponse[Event]:
    result_items = await event_crud.list(
        filter_study_id=study_access.study.id,
        hide_completed=hide_completed,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await event_crud.count(
            filter_study_id=study_access.study.id,
            hide_completed=hide_completed,
        ),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )


@fast_api_event_router.post(
    "/study/{study_id}/event",
    response_model=Event,
    description=f"Create a new event.",
)
async def create_event(
    event: EventCreateAPI,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> Event:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to create new event",
        )
    event_create = EventCreate(**event.model_dump(), study_id=study_access.study.id)
    return await event_crud.create(
        event_create,
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
