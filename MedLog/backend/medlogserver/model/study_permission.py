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
from sqlmodel import (
    Field,
    select,
    delete,
    Column,
    JSON,
    SQLModel,
    UniqueConstraint,
    Relationship,
)
from datetime import datetime
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.db.user import User
from medlogserver.model.study import Study


log = get_logger()
config = Config()


class StudyPermissonUpdate(MedLogBaseModel, table=False):
    is_study_viewer: bool = Field(
        default=True,
        description="This is the minimal access to a study. The user can see all data but can not alter anything",
    )
    is_study_interviewer: bool = Field(
        default=False,
        description="Study interviewers can create new interview entries for this study.",
    )
    is_study_admin: bool = Field(
        default=False,
        description="Study admins can give access to the study to new users.",
    )


class StudyPermissonBase(StudyPermissonUpdate, table=False):
    study_id: uuid.UUID = Field(foreign_key="study.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    is_study_viewer: bool = Field(
        default=True,
        description="This is the minimal access to a study. The user can see all data but can not alter anything",
    )
    is_study_interviewer: bool = Field(
        default=False,
        description="Study interviewers can create new interview entries for this study.",
    )
    is_study_admin: bool = Field(
        default=False,
        description="Study admins can give access to the study to new users.",
    )

    @field_validator("user_id", "study_id")
    @classmethod
    def foreign_key_to_uuid(cls, v: str | uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        return MedLogBaseModel.id_to_uuid(v, info)


class StudyPermissionRead(StudyPermissonBase, table=False):
    id: uuid.UUID = Field()
    user_ref: User = Field()
    study_ref: Study = Field()


class StudyPermisson(StudyPermissonBase, BaseTable, table=True):
    __tablename__ = "study_permission"
    __table_args__ = (
        UniqueConstraint(
            "study_id", "user_id", name="One permission entry per user/study only"
        ),
    )
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    user_ref: User = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
    study_ref: Study = Relationship(
        sa_relationship_kwargs={
            "lazy": "joined",
            "viewonly": True,
        }
    )
