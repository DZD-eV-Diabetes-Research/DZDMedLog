from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import (
    validate_email,
    validator,
    StringConstraints,
    field_validator,
    ValidationInfo,
)
import datetime
from fastapi import Depends
from typing import Optional
from sqlmodel import Field, UniqueConstraint

import enum
import uuid
from uuid import UUID

from medlogserver.config import Config as AppConfig
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel

log = get_logger()
config = AppConfig()


_name_annotation = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, pattern=r"^[a-zA-Z0-9- ]+$", max_length=64
    ),
]

_name_field = Field(
    default=None,
    index=True,
    unique=False,
    description="A (study wide) unique name for the Event.",
    schema_extra={"examples": ["visit01", "TI12"]},
)


_event_type_annotation = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)
]

_external_id_annotation = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=128)
]


class EventTypeMode(str, enum.Enum):
    """How the event type of an interview is set (issue #388).

    The available event types come from the server config `EVENT_TYPES`.
    """

    FIXED = "fixed"  # the event's type is always used, the interviewer can not change it
    DEFAULT = "default"  # the event's type is pre-filled, the interviewer can change it
    REQUIRED_CHOICE = "required_choice"  # no pre-fill, the interviewer must choose


class EventBase(MedLogBaseModel, table=False):
    order_position: Optional[int] = Field(
        default=None,
        description="A ranked value to sort this event if its contained in list of events. If not provided, it will default to highest sort order compared to existing events in this study.",
    )
    external_id: Optional[_external_id_annotation] = Field(
        default=None,
        description=(
            "Optional free text ID to map this event to the ID used in external systems "
            "(e.g. an eCRF). Only for mapping, the authoritative identifier stays `id`."
        ),
        schema_extra={"examples": ["1201", "V01"]},
    )
    event_type_mode: Optional[EventTypeMode] = Field(
        default=None,
        description=(
            "How the event type of the interviews of this event is set. "
            "`fixed`: always `event_type`, can not be changed. "
            "`default`: pre-filled with `event_type`, can be changed. "
            "`required_choice`: no pre-fill, has to be chosen for every interview. "
            "`null`: the event does not track an event type. "
            "Only available if the server config `EVENT_TYPES` is set."
        ),
    )
    event_type: Optional[_event_type_annotation] = Field(
        default=None,
        description=(
            "The event type for the modes `fixed` and `default`. Must be one of the "
            "configured `EVENT_TYPES`. Must be `null` for the mode `required_choice` "
            "or if no mode is set."
        ),
        schema_extra={"examples": ["on-site visit"]},
    )

    @field_validator("external_id", mode="after")
    @classmethod
    def empty_external_id_to_none(cls, v: Optional[str]) -> Optional[str]:
        return v or None


class EventCreateAPI(EventBase, table=False):
    name: _name_annotation = _name_field


class EventUpdate(EventBase, table=False):
    name: Optional[_name_annotation] = _name_field


class EventCreate(EventCreateAPI, TimestampModel, table=False):
    study_id: UUID = Field(foreign_key="study.id")
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)

    @field_validator("study_id")
    @classmethod
    def foreign_key_to_uuid(cls, v: str | uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        return MedLogBaseModel.id_to_uuid(v, info)


class EventRead(EventCreate, table=False):
    id: uuid.UUID = Field()


class EventReadPerProband(EventRead, table=False):
    proband_id: str = Field(description="the ID of the proband.")
    proband_interview_count: int = Field(
        description="How many interviews has the proband in this event."
    )


class Event(EventRead, table=True):
    __tablename__ = "event"
    __table_args__ = (
        UniqueConstraint("name", "study_id", name="unique_eventname_per_study"),
    )
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    class Config:
        # default sorting order
        order_by = "name"


class EventExport(EventRead, table=False):
    created_at: datetime.datetime = Field(exclude=True)
    study_id: UUID = Field(exclude=True)
    # The event type that was actually used is exported per interview
    # (`interview.event_type`). The event's settings would only add a confusing
    # second `event_type` column.
    event_type_mode: Optional[EventTypeMode] = Field(default=None, exclude=True)
    event_type: Optional[str] = Field(default=None, exclude=True)


def check_event_type_settings(
    event_type_mode: Optional[EventTypeMode], event_type: Optional[str]
) -> None:
    """Raise a ValueError if the event type settings of an event are not valid."""
    if event_type_mode is None:
        if event_type is not None:
            raise ValueError(
                "'event_type' can only be set together with the 'event_type_mode' "
                f"'{EventTypeMode.FIXED.value}' or '{EventTypeMode.DEFAULT.value}'."
            )
        return
    if not config.EVENT_TYPES:
        raise ValueError(
            "Event types are not available on this server ('EVENT_TYPES' is not configured)."
        )
    if event_type_mode == EventTypeMode.REQUIRED_CHOICE:
        if event_type is not None:
            raise ValueError(
                f"'event_type' must not be set for the 'event_type_mode' "
                f"'{EventTypeMode.REQUIRED_CHOICE.value}'."
            )
        return
    if event_type is None:
        raise ValueError(
            f"'event_type' is required for the 'event_type_mode' '{event_type_mode.value}'."
        )
    if event_type not in config.EVENT_TYPES:
        raise ValueError(
            f"Unknown event type '{event_type}'. Available event types: {config.EVENT_TYPES}"
        )


def resolve_interview_event_type(
    event: "Event",
    requested_event_type: Optional[str],
    stored_event_type: Optional[str] = None,
) -> Optional[str]:
    """Return the event type an interview of `event` gets, or raise a ValueError.

    `requested_event_type` is the value sent by the client, `None` if it was left out.
    `stored_event_type` is the value the interview already has (`None` on creation).
    A type that is left out keeps the stored one, so interviews keep their type when
    the event settings change later.
    """
    mode = event.event_type_mode
    if requested_event_type is not None:
        if mode is None:
            raise ValueError(
                f"Event '{event.name}' does not track an event type, 'event_type' must not be set."
            )
        if mode == EventTypeMode.FIXED:
            if requested_event_type != event.event_type:
                raise ValueError(
                    f"Event '{event.name}' has the fixed event type '{event.event_type}', "
                    f"it can not be changed to '{requested_event_type}'."
                )
        elif requested_event_type not in config.EVENT_TYPES:
            raise ValueError(
                f"Unknown event type '{requested_event_type}'. "
                f"Available event types: {config.EVENT_TYPES}"
            )
        return requested_event_type
    if stored_event_type is not None:
        return stored_event_type
    if mode in (EventTypeMode.FIXED, EventTypeMode.DEFAULT):
        return event.event_type
    if mode == EventTypeMode.REQUIRED_CHOICE:
        raise ValueError(
            f"Event '{event.name}' requires an event type, 'event_type' must be set. "
            f"Available event types: {config.EVENT_TYPES}"
        )
    return None
