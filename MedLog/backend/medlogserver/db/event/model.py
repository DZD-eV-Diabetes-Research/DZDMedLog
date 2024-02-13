from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.event_auth import EventAuthRefreshTokenCRUD


log = get_logger()
config = Config()


_name_annotation = Annotated[
    Optional[str],
    StringConstraints(strip_whitespace=True, pattern=r"^[a-zA-Z0-9-]+$", max_length=64),
]


class EventUpdate(Base, table=False):
    name: _name_annotation = Field(
        default=None,
        index=True,
        unique=True,
        schema_extra={"examples": ["visit01", "TI12"]},
    )
    completed: bool = Field(
        default=False,
        description="Is the event completed. E.g. All study participants have been interviewed.",
    )


class Event(EventUpdate, BaseTable, table=True):
    __tablename__ = "event"
    study_id: UUID = Field(foreign_key="study.id")
    name: _name_annotation = Field(
        index=True,
        unique=True,
        schema_extra={"examples": ["visit01", "TI12"]},
    )
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
