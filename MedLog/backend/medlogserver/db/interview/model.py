from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
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
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.event.model import Event

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.interview_auth import InterviewAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class InterviewCreate(Base, table=False):
    event_id: str = Field(foreign_key="event.id")
    proband_external_id: str = Field()
    interview_start_time_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    interview_end_time_utc: datetime = Field(default=None)
    proband_has_taken_meds: bool = Field()
    interview_number: int = Field(
        description="TB: This field is still kind of mysterious to me. In the user interview video the user just filled it with some number. Maybe a process we can automize (shameless plug: https://git.apps.dzd-ev.org/dzdpythonmodules/ptan)?"
    )


class InterviewUpdate(InterviewCreate, table=False):
    pass


class Interview(InterviewCreate, table=True):
    __tablename__ = "interview"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
