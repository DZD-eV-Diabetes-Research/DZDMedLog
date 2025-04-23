from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import (
    validate_email,
    validator,
    StringConstraints,
    field_validator,
    ValidationInfo,
)
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from sqlalchemy.sql.operators import is_not, is_
from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.event import Event

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.interview_auth import InterviewAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class InterviewCreateAPI(MedLogBaseModel, table=False):
    proband_external_id: str = Field(
        description="A unique ID given to the proband from the studies external proband management system"
    )
    interview_start_time_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        description="Defaults to current time.",
    )
    interview_end_time_utc: Optional[datetime] = Field(default=None)
    proband_has_taken_meds: bool = Field()


class InterviewCreate(InterviewCreateAPI, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_id: uuid.UUID = Field(foreign_key="event.id")
    interviewer_user_id: uuid.UUID = Field(foreign_key="user.id")


class InterviewUpdate(InterviewCreateAPI, table=False):
    pass


class Interview(InterviewCreate, BaseTable, TimestampModel, table=True):
    __tablename__ = "interview"
    id: uuid.UUID = Field(
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class InterviewExport(InterviewCreate, table=False):
    created_at: datetime = Field(exclude=True)
    event_id: uuid.UUID = Field(foreign_key="event.id", exclude=True)
