from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import (
    validate_email,
    validator,
    StringConstraints,
    field_validator,
    ValidationInfo,
)
from fastapi import Depends
from typing import Optional
from sqlmodel import Field, UniqueConstraint

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable

log = get_logger()
config = Config()


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


class EventCreateAPI(MedLogBaseModel, table=False):
    name: _name_annotation = _name_field
    order_position: Optional[int] = Field(
        default=None,
        description="A ranked value to sort this event if its contained in list of events. If not provided, it will default to highest sort order compared to existing events in this study.",
    )


class EventUpdate(EventCreateAPI, table=False):
    name: Optional[_name_annotation] = _name_field
    completed: Optional[bool] = Field(
        default=False,
        description="Is the event completed. E.g. All study participants have been interviewed.",
    )


class EventCreate(EventUpdate, table=False):
    name: _name_annotation = _name_field

    study_id: UUID = Field(foreign_key="study.id")
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)

    @field_validator("study_id")
    @classmethod
    def foreign_key_to_uuid(cls, v: str | uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        return MedLogBaseModel.id_to_uuid(v, info)


class EventRead(EventCreate, BaseTable, table=False):
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
