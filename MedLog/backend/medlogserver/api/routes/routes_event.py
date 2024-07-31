from typing import Annotated, Sequence, List, Type
from datetime import datetime, timedelta, timezone
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


from fastapi import Depends, APIRouter


from medlogserver.db.user import User


from medlogserver.model.event import (
    Event,
    EventUpdate,
    EventCreate,
    EventRead,
    EventCreateAPI,
    EventReadPerProband,
)
from medlogserver.db.interview import InterviewCRUD, Interview
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

EventQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Event, default_order_by_attr="order_position"
)


@fast_api_event_router.get(
    "/study/{study_id}/event",
    response_model=PaginatedResponse[Event],
    description=f"List all events of a study.",
)
async def list_events(
    hide_completed: bool = Query(False),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(EventQueryParams),
) -> PaginatedResponse[EventRead]:
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
    response_model=EventRead,
    description=f"Create a new event.",
)
async def create_event(
    event: EventCreateAPI,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> EventRead:
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to create new event",
        )
    if event.order_position is None:
        event.order_position = 0
        all_events = await event_crud.list(filter_study_id=study_access.study.id)
        if all_events:
            highest_existing_order_position = max(
                [e.order_position for e in all_events]
            )
            event.order_position = highest_existing_order_position + 10

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
    response_model=EventRead,
    description=f"Update existing event",
)
async def update_event(
    event_id: uuid.UUID,
    event: EventUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> EventRead:
    if not study_access.user_is_study_interviewer():
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
    event_id: uuid.UUID,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
):
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


@fast_api_event_router.post(
    "/study/{study_id}/event/order",
    response_model=List[EventRead],
    description=f"This endpoint accepts a list of event objects or IDs and assigns a sequential integer to each event's order_position attribute based on their order in the input list. The first event in the list will be assigned `order_position`: `10`, the second event will be assigned  `order_position`: `20`, and so on.",
)
async def reorder_events(
    events: List[EventRead | Event | uuid.UUID],
    reverse: bool = Query(
        False, description="Reorder events in the reversed order as given"
    ),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> List[Event]:
    if not study_access.user_is_study_interviewer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to reorder events",
        )
    event_ids = []
    for event_or_id in events:
        if isinstance(event_or_id, (EventRead, Event)):
            event_ids.append(event_or_id.id)
        elif isinstance(event_or_id, str):
            event_ids.append(uuid.UUID(event_or_id))
        elif isinstance(event_or_id, uuid.UUID):
            event_ids.append(event_or_id)
    if reverse:
        event_ids = list(reversed(event_ids))
    return await event_crud.reorder_events(event_ids)


@fast_api_event_router.get(
    "/study/{study_id}/proband/{proband_id}/event",
    response_model=PaginatedResponse[EventReadPerProband],
    description=f"List all events and include the interview count on a per proband level.",
)
async def list_events_per_proband(
    proband_id: str = Path(),
    exlude_empty_events: bool = Query(
        default=False,
        description="If set to `true`, only events with at least one existing interview for the given `proband_id` will be listed.",
    ),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(EventCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(EventQueryParams),
) -> PaginatedResponse[EventReadPerProband]:
    result_items = await event_crud.list_by_proband(
        proband_id=proband_id,
        exlude_empty_events=exlude_empty_events,
        filter_study_id=study_access.study.id,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await event_crud.count(
            filter_study_id=study_access.study.id,
        ),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )
