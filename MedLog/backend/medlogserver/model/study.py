from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
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
from medlogserver.model._base_model import MedLogBaseModel, BaseTable


log = get_logger()
config = Config()


class StudyCreateAPI(MedLogBaseModel, table=False):
    display_name: Optional[str] = Field(
        default=None,
        index=True,
        max_length=128,
        unique=True,
        schema_extra={
            "examples": [
                "Prädiabetes-Lebensstil-Interventions-Studie (PLIS)",
                "BARIA-DDZ-Studie",
            ]
        },
    )
    no_permissions: bool = Field(
        default=config.APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT,
        description="If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study. Admin access still need to be allocated explicit.",
    )


class StudyUpdate(StudyCreateAPI):
    pass

    deactivated: bool = Field(default=False)


class StudyCreate(StudyUpdate):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)


class Study(StudyCreate, BaseTable, table=True):
    __tablename__ = "study"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class StudyExport(Study, table=False):
    deactivated: bool = Field(exclude=True)
    no_permissions: bool = Field(exclude=True)
