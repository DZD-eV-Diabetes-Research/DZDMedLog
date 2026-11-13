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
from pydantic import BaseModel, Field, ConfigDict

from fastapi import Depends, APIRouter


from medlogserver.db.user import User


from medlogserver.model.event import (
    Event,
    EventUpdate,
    EventCreate,
    EventRead,
    EventCreateAPI,
    EventReadPerProband,
    check_event_type_settings,
)
from medlogserver.db.interview import InterviewCRUD, Interview
from medlogserver.db.event import EventCRUD


from medlogserver.config import Config
from medlogserver.api.study_access import (
    user_has_study_access,
    UserStudyAccess,
)
from medlogserver.api.base import HTTPErrorResponeRepresentation
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)


class _EventNotEmptyDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    error: str = Field(default="event not empty", examples=["event not empty"])
    interview_ids: List[uuid.UUID] = Field(
        description="IDs of all interviews that must be deleted before this event can be removed.",
        examples=[["a1b2c3d4-0000-0000-0000-000000000001", "a1b2c3d4-0000-0000-0000-000000000002"]],
    )


class EventNotEmptyErrorResponse(BaseModel):
    detail: _EventNotEmptyDetail

def _assert_valid_event_type_settings(event_type_mode, event_type) -> None:
    try:
        check_event_type_settings(event_type_mode, event_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


_event_type_settings_error_response = {
    "model": HTTPErrorResponeRepresentation,
    "description": "`event_type_mode` and `event_type` do not fit together, or `event_type` is not one of the configured `EVENT_TYPES`.",
}


def _event_name_conflict_exception(event_name: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Event with name '{event_name}' already exists in this study",
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
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(EventQueryParams),
) -> PaginatedResponse[EventRead]:
    result_items = await event_crud.list(
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


@fast_api_event_router.post(
    "/study/{study_id}/event",
    response_model=EventRead,
    description=f"Create a new event.",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": HTTPErrorResponeRepresentation,
            "description": "An event with the requested `name` already exists in this study.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: _event_type_settings_error_response,
    },
)
async def create_event(
    event: EventCreateAPI,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> EventRead:
    study_access.assert_study_is_not_deactivated("its events")
    if not study_access.user_is_study_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create new event",
        )
    _assert_valid_event_type_settings(event.event_type_mode, event.event_type)
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
        raise_custom_exception_if_exists=_event_name_conflict_exception(event.name),
    )


@fast_api_event_router.patch(
    "/study/{study_id}/event/{event_id}",
    response_model=EventRead,
    description=f"Update existing event",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPErrorResponeRepresentation,
            "description": "No event with the given `event_id` exists in this study.",
        },
        status.HTTP_409_CONFLICT: {
            "model": HTTPErrorResponeRepresentation,
            "description": "Another event of this study already has the requested `name`.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: _event_type_settings_error_response,
    },
)
async def update_event(
    event_id: uuid.UUID,
    event: EventUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> EventRead:
    study_access.assert_study_is_not_deactivated("its events")
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update event",
        )
    event_not_found_exception = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No event with id '{event_id}'",
    )
    existing_event = await event_crud.get(
        event_id, raise_exception_if_none=event_not_found_exception
    )
    # The study access check only covers the study in the path, so make sure the event
    # actually belongs to it.
    if existing_event.study_id != study_access.study.id:
        raise event_not_found_exception

    # The event type settings are only checked when they are changed, so an event whose
    # type was removed from the server config can still be renamed or reordered.
    if {"event_type_mode", "event_type"} & event.model_fields_set:
        if not study_access.user_is_study_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change the event type settings of an event",
            )
        _assert_valid_event_type_settings(
            (
                event.event_type_mode
                if "event_type_mode" in event.model_fields_set
                else existing_event.event_type_mode
            ),
            (
                event.event_type
                if "event_type" in event.model_fields_set
                else existing_event.event_type
            ),
        )

    # Explicit pre-check for a clean error message (issue #382: a rename to a taken name
    # used to surface as a 500 from the unique index); the CRUD still maps the unique
    # constraint violation to the same 409 in case of a race.
    if "name" in event.model_fields_set and event.name is not None:
        event_with_same_name = await event_crud.get_by_name(
            study_id=study_access.study.id, event_name=event.name
        )
        if event_with_same_name is not None and event_with_same_name.id != event_id:
            raise _event_name_conflict_exception(event.name)

    return await event_crud.update(
        id_=event_id,
        update_obj=event,
        raise_exception_if_not_exists=event_not_found_exception,
        raise_custom_exception_if_exists=_event_name_conflict_exception(event.name),
    )


@fast_api_event_router.delete(
    "/study/{study_id}/event/{event_id}",
    summary="Delete an event",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Event deleted successfully."},
        status.HTTP_401_UNAUTHORIZED: {
            "model": HTTPErrorResponeRepresentation,
            "description": "Not authenticated.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": HTTPErrorResponeRepresentation,
            "description": "Caller is not a study admin or global admin.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": HTTPErrorResponeRepresentation,
            "description": "No event with the given `event_id` exists in this study.",
        },
        status.HTTP_409_CONFLICT: {
            "model": EventNotEmptyErrorResponse,
            "description": (
                "The event still has interviews attached. "
                "The response body lists their IDs under `detail.interview_ids`. "
                "Delete all interviews first, then retry."
            ),
        },
    },
)
async def delete_event(
    event_id: Annotated[uuid.UUID, Path(description="ID of the event to delete.")],
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
):
    """
    Delete a study event permanently.

    The event must have **no interviews** attached. If any exist, a `409` is returned with
    their IDs — delete them first via
    `DELETE /study/{study_id}/event/{event_id}/interview/{interview_id}`.

    Requires **study admin** or global **medlog-admin** role.
    """
    study_access.assert_study_is_not_deactivated("its events")
    if not study_access.user_is_study_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete event",
        )
    await event_crud.get(
        event_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No event with id '{event_id}'",
        ),
    )
    interviews = await interview_crud.list(filter_event_id=event_id)
    if interviews:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "event not empty",
                "interview_ids": [
                    str(i.id) for i in interviews
                ],
            },
        )
    await event_crud.delete(id_=event_id)


@fast_api_event_router.post(
    "/study/{study_id}/event/order",
    response_model=List[EventRead],
    description=f"This endpoint accepts a list of event objects or IDs and assigns a sequential integer to each event's order_position attribute based on their order in the input list. The first event in the list will be assigned `order_position`: `10`, the second event will be assigned  `order_position`: `20`, and so on.",
)
async def reorder_events(
    events: List[EventRead | Event | uuid.UUID | str],
    reverse: bool = Query(
        False, description="Reorder events in the reversed order as given"
    ),
    study_access: UserStudyAccess = Security(user_has_study_access),
    event_crud: EventCRUD = Depends(EventCRUD.get_crud),
) -> List[Event]:
    study_access.assert_study_is_not_deactivated("the order of its events")
    # `user_is_study_interviewer` is a method: without the parentheses the bound method
    # object is always truthy, `not ...` always False, and the check never fired - every
    # user with plain read access to the study could rewrite the event order.
    if not study_access.user_is_study_interviewer():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
        proband_external_id_normalization=study_access.study.proband_external_id_normalization,
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
