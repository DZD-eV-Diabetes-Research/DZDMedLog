from typing import AsyncGenerator, List, Optional, Literal, Dict, Sequence
from pydantic import SecretStr, Json
from fastapi import Depends
import contextlib
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from sqlmodel import Field, select, delete, Column, JSON
import uuid
from oauthlib.oauth2 import OAuth2Token
from medlogserver.db.user import User
from medlogserver.db.user_auth import UserAuth
from medlogserver.model.user_auth_external_oidc_token import UserAuthExternalOIDCToken
from medlogserver.db._base_crud import create_crud_base

log = get_logger()
config = Config()


class UserAuthExternalOIDCTokenCRUD(
    create_crud_base(
        table_model=UserAuthExternalOIDCToken,
        read_model=UserAuthExternalOIDCToken,
        create_model=UserAuthExternalOIDCToken,
        update_model=UserAuthExternalOIDCToken,
    )
):

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

    async def create(
        self,
        obj: UserAuthExternalOIDCToken,
        exists_ok: bool = False,
        raise_custom_exception_if_exists: Exception = None,
    ) -> UserAuthExternalOIDCToken:
        query = select(UserAuthExternalOIDCToken).where(
            UserAuthExternalOIDCToken.oauth_token == obj.oauth_token
        )
        results = await self.session.exec(statement=query)
        existing_oidc_token: UserAuthExternalOIDCToken = results.one_or_none()
        if existing_oidc_token and not exists_ok:
            raise ValueError(f"Token allready exists (id:'{existing_oidc_token.id}')")
        elif existing_oidc_token and exists_ok:
            return existing_oidc_token

        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
