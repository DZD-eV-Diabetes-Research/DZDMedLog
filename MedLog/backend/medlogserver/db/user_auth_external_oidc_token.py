from typing import AsyncGenerator, List, Optional, Literal
from pydantic import SecretStr, Json

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable
from medlogserver.db.base import AsyncSession
from sqlmodel import Field, select, delete
from uuid import UUID

log = get_logger()
config = Config()


class UserAuthExternalOIDCToken(BaseTable, table=True):
    __tablename__ = "user_auth_external_oidc_token"
    oidc_provider_name: str = Field(index=True)
    token_encoded: Json = Field(default=None, index=True)
    valid_until_timestamp: int = Field(default=None)
    user_id: int = Field(default=None, foreign_key="user.id")
    disabled: bool = Field(default=False)
    user_auth_base_uuid: UUID = Field(default=None, foreign_key="user_auth_base.uuid")
