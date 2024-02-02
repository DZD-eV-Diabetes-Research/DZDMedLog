from typing import AsyncGenerator, List, Optional, Literal, Dict, Sequence
from pydantic import SecretStr, Json
from fastapi import Depends
import contextlib
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from sqlmodel import Field, select, delete, Column, JSON
import uuid
from oauthlib.oauth2 import OAuth2Token
from medlogserver.db.user import User
from medlogserver.db.user_auth import (
    get_user_auth_crud,
    UserAuth,
    UserAuthCreate,
    UserAuthCRUD,
    UserAuthRefreshToken,
    UserAuthRefreshTokenCRUD,
    get_user_auth_refresh_token_crud,
    AllowedAuthSourceTypes,
)

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
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    oidc_provider_name: str = Field(index=True)
    oauth_token: Dict = Field(default=None, sa_column=Column(type_=JSON))
    # valid_until_timestamp: int = Field(default=None)
    deactivated: bool = Field(default=False)
    user_auth_id: uuid.UUID = Field(default=None, foreign_key="user_auth.id")


class UserAuthExternalOIDCTokenCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user_id(
        self,
        user_id: str | uuid.UUID,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuthExternalOIDCToken]:
        query = (
            select(UserAuthExternalOIDCToken)
            .join(UserAuth)
            .where(UserAuth.user_id == user_id)
        )

        results = await self.session.exec(statement=query)
        external_oidc_tokens: Sequence[UserAuthExternalOIDCToken] = results.all()
        if external_oidc_tokens is None and raise_exception_if_none:
            raise raise_exception_if_none
        return external_oidc_tokens

    async def list_by_user_auth(
        self,
        user_auth_id: str | uuid.UUID,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuthExternalOIDCToken]:
        query = select(UserAuthExternalOIDCToken).where(
            UserAuthExternalOIDCToken.user_auth_id == user_auth_id
        )

        results = await self.session.exec(statement=query)
        external_oidc_tokens: Sequence[UserAuthExternalOIDCToken] = results.all()
        if external_oidc_tokens is None and raise_exception_if_none:
            raise raise_exception_if_none
        return external_oidc_tokens

    async def list_by_user_name(
        self,
        user_name: str,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuthExternalOIDCToken]:
        query = (
            select(UserAuthExternalOIDCToken)
            .join(UserAuth)
            .join(User)
            .where(User.user_name == user_name)
        )
        results = await self.session.exec(statement=query)
        external_oidc_tokens: Sequence[UserAuthExternalOIDCToken] = results.all()
        if external_oidc_tokens is None and raise_exception_if_none:
            raise raise_exception_if_none
        return external_oidc_tokens

    async def get(
        self,
        id_: str | uuid.UUID,
        raise_exception_if_not_exists: Exception = None,
    ) -> UserAuthExternalOIDCToken:
        query = select(UserAuthExternalOIDCToken).where(
            UserAuthExternalOIDCToken.id == id_
        )
        results = await self.session.exec(statement=query)
        external_oidc_token: UserAuthExternalOIDCToken = results.one_or_none()

        if not external_oidc_token and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        return external_oidc_token

    async def create(
        self,
        oidc_token: UserAuthExternalOIDCToken,
        exists_ok: bool = False,
        raise_exception_if_exists: Exception = None,
    ) -> UserAuthExternalOIDCToken:
        query = select(UserAuthExternalOIDCToken).where(
            UserAuthExternalOIDCToken.oauth_token == oidc_token.oauth_token
        )
        results = await self.session.exec(statement=query)
        existing_oidc_token: UserAuthExternalOIDCToken = results.one_or_none()
        if existing_oidc_token and not exists_ok:
            raise ValueError(f"Token allready exists (id:'{existing_oidc_token.id}')")
        elif existing_oidc_token and exists_ok:
            return existing_oidc_token

        self.session.add(oidc_token)
        await self.session.commit()
        await self.session.refresh(oidc_token)
        return oidc_token

    async def delete(
        self,
        id_: str | uuid.UUID,
        raise_exception_if_not_exists=None,
    ) -> Literal[True] | None:
        if raise_exception_if_not_exists:
            self.get(id_, raise_exception_if_not_exists=raise_exception_if_not_exists)
        del_statement = delete(UserAuthExternalOIDCToken).where(
            UserAuthExternalOIDCToken.id == id_
        )
        await self.session.exec(statement=del_statement)
        return True


async def get_user_auth_external_oidc_token_crud(
    session: AsyncSession = Depends(get_async_session),
) -> UserAuthExternalOIDCTokenCRUD:
    yield UserAuthExternalOIDCTokenCRUD(session=session)


get_user_auth_external_oidc_token_crud_context = contextlib.asynccontextmanager(
    get_user_auth_external_oidc_token_crud
)
