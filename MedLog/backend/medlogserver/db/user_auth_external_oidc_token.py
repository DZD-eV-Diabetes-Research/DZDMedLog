from typing import AsyncGenerator, List, Optional, Literal, Dict
from pydantic import SecretStr, Json

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from sqlmodel import Field, select, delete, Column, JSON
import uuid

log = get_logger()
config = Config()


class UserAuthExternalOIDCToken(BaseTable, table=True):
    __tablename__ = "user_auth_external_oidc_token"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        #sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    oidc_provider_name: str = Field(index=True)
    token_encoded: Dict = Field(default=None, sa_column=Column(JSON))
    valid_until_timestamp: int = Field(default=None)
    disabled: bool = Field(default=False)
    user_auth_base_uuid: uuid.UUID = Field(default=None, foreign_key="user_auth.id")
