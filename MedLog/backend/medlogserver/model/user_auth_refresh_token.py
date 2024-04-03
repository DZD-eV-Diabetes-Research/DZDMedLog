# Basics
from typing import AsyncGenerator, List, Optional, Literal, Sequence

# Libs
import enum
import uuid
from pydantic import SecretStr
from sqlmodel import Field, Column, Enum
from passlib.context import CryptContext

# Internal
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import BaseTable
from medlogserver.model.user import User


log = get_logger()
config = Config()


class _UserAuthRefreshTokenBase(BaseTable, table=False):
    user_auth_id: uuid.UUID = Field(default=None, foreign_key="user_auth.id")


class UserAuthRefreshTokenUpdate(_UserAuthRefreshTokenBase, table=False):
    deactivated: bool = Field(default=False)


class UserAuthRefreshTokenCreate(_UserAuthRefreshTokenBase, table=False):
    token_encoded: str = Field()
    valid_until_timestamp: int = Field(default=None)


class UserAuthRefreshToken(
    UserAuthRefreshTokenCreate, UserAuthRefreshTokenUpdate, table=True
):
    __tablename__ = "user_auth_access_token"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
