from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from fastapi import Depends
from typing import Optional
from sqlmodel import Field

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable

log = get_logger()
config = Config()


_name_annotation = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[a-zA-Z0-9-]+$", max_length=64),
]


class EventCreateAPI(MedLogBaseModel, table=False):
    name: _name_annotation = Field(
        default=None,
        index=True,
        unique=True,
        schema_extra={"examples": ["visit01", "TI12"]},
    )


class EventUpdate(EventCreateAPI, table=False):
    name: Optional[_name_annotation] = Field(
        default=None,
        index=True,
        unique=True,
        schema_extra={"examples": ["visit01", "TI12"]},
    )
    completed: Optional[bool] = Field(
        default=False,
        description="Is the event completed. E.g. All study participants have been interviewed.",
    )


class EventCreate(EventUpdate, table=False):
    name: _name_annotation = Field(
        default=None,
        index=True,
        unique=True,
        schema_extra={"examples": ["visit01", "TI12"]},
    )

    study_id: UUID = Field(foreign_key="study.id")
    id: Optional[uuid.UUID] = Field()


class EventRead(EventCreate, table=False):
    id: uuid.UUID = Field()


class Event(EventRead, BaseTable, table=True):
    __tablename__ = "event"
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
