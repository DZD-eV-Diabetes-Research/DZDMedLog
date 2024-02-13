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
from medlogserver.db.base import Base, BaseTable


log = get_logger()
config = Config()


class StudyBase(Base, table=False):

    display_name: Optional[str] = Field(
        default=None,
        index=True,
        max_length=128,
        schema_extra={
            "examples": [
                "Prädiabetes-Lebensstil-Interventions-Studie (PLIS)",
                "BARIA-DDZ-Studie",
            ]
        },
    )

    deactivated: bool = Field(default=False)

    no_permissions: bool = Field(
        default=False,
        description="If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study.  Admin access still need to be allocated explicit.",
    )

    @model_validator(mode="after")
    def val_display_name(self, values):
        """if no display name is set for now, we copy the identifying `name`"""
        if values["display_name"] is None:
            values["display_name"] == values["name"]
        return values


class StudyUpdate(StudyBase):
    pass


class StudyCreate(StudyUpdate):
    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, to_lower=True, pattern=r"^[a-zA-Z0-9-]+$"
        ),
    ] = Field(
        description="The identifiying name of the study. This can not be changed later. Must be a '[Slug](https://en.wikipedia.org/wiki/Clean_URL#Slug)'; A human and machine reable string containing no spaces, only numbers, lowered latin-script-letters and dashes. If you need to change the name later, use the display name.",
        index=True,
        max_length=64,
        unique=True,
        schema_extra={"examples": ["plis", "baria-ddz"]},
    )


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
