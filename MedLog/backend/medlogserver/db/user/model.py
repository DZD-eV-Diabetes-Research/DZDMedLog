from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.user_auth import UserAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class UserBase(BaseModel, table=False):
    email: Optional[str] = Field(
        default=None,
        index=True,
        max_length=320,
        schema_extra={"examples": ["clara@uni.wroc.pl", "titor@time.com"]},
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=128,
        min_length=2,
        schema_extra={"examples": ["Clara Immerwahr", "John Titor"]},
    )


class UserUpdateByUser(UserBase, table=False):
    pass


class UserUpdate(UserBase, table=False):
    id: Optional[uuid.UUID] = Field(default=None)


class UserUpdateByAdmin(UserUpdate, table=False):
    roles: List[str] = Field(default=[], sa_column=Column(JSON))
    deactivated: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)


class _UserValidate(UserBase, table=False):
    @validator("email")
    def validmail(cls, email):
        validate_email(email)
        return email

    @model_validator(mode="after")
    def val_display_name(self, values):
        """if no display name is set for now, we copy the identifying `user_name`"""
        if self.display_name is None:
            self.display_name = self.user_name
        return values


class _UserWithName(UserBase, table=False):
    user_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            to_lower=True,
            pattern=r"^[a-zA-Z0-9-]+$",
            max_length=128,
            min_length=3,
        ),
    ] = Field(
        default=None,
        index=True,
        unique=True,
        schema_extra={"examples": ["clara.immerwahr", "titor.extern.times"]},
    )


class UserCreate(_UserWithName, _UserValidate, table=False):
    pass


class User(_UserWithName, UserUpdateByAdmin, BaseTable, table=True):
    __tablename__ = "user"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
