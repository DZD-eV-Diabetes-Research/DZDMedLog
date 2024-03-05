# Basics
from typing import AsyncGenerator, List, Optional, Literal, Sequence

# Libs
import enum
import uuid
import contextlib
from pydantic import SecretStr, Json
from fastapi import Depends, HTTPException, status
from sqlmodel import Field, select, delete, Enum, Column
from passlib.context import CryptContext

# Internal
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.model.user import User
from medlogserver.model.user_auth import (
    UserAuth,
)
from medlogserver.model.user_auth_refresh_token import (
    UserAuthRefreshToken,
    UserAuthRefreshTokenCreate,
    UserAuthRefreshTokenUpdate,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class UserAuthRefreshTokenCRUD(
    create_crud_base(
        table_model=UserAuthRefreshToken,
        read_model=UserAuthRefreshToken,
        create_model=UserAuthRefreshTokenCreate,
        update_model=UserAuthRefreshTokenUpdate,
    )
):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        id: str | uuid.UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> UserAuthRefreshToken:
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        if not show_deactivated:
            query = query.where(UserAuthRefreshToken.deactivated == False)
        results = await self.session.exec(statement=query)
        user_auth_refresh_token: UserAuthRefreshToken | None = results.one_or_none()
        if user_auth_refresh_token is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user_auth_refresh_token

    async def list_by_user(
        self,
        user_id: str | uuid.UUID,
    ) -> List[UserAuthRefreshToken]:
        query = select(UserAuthRefreshToken).where(
            UserAuthRefreshToken.user_id == user_id
        )
        results = await self.session.exec(statement=query)
        user_auth_refresh_tokens: Sequence[UserAuthRefreshToken] = results.all()

        return list(user_auth_refresh_tokens)

    async def delete(
        self, id: str | uuid.UUID, raise_exception_if_not_exists=None
    ) -> None | Literal[True]:
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth = results.one_or_none()

        if user_auth is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        else:
            query = delete(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
            await self.session.exec(statement=query)
            await self.session.commit()
            return True

    async def update(
        self,
        user_auth_access_token_update: UserAuthRefreshTokenUpdate,
        id: str | uuid.UUID = None,
    ) -> UserAuthRefreshToken:
        id = id if id is not None else user_auth_access_token_update.id
        if id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth_refresh_token: UserAuthRefreshToken = results.one_or_none()
        for k, v in user_auth_access_token_update.model_dump(
            exclude_unset=True
        ).items():
            if k in UserAuthRefreshTokenUpdate.model_fields.keys():
                setattr(user_auth_refresh_token, k, v)

        self.session.add(user_auth_refresh_token)
        await self.session.commit()
        await self.session.refresh(user_auth_refresh_token)
        return user_auth_refresh_token

    async def disable_by_user_id(self, user_id: uuid.UUID):
        """Disable all refresh token from a certain user

        Args:
            user_id (uuid.UUID): _description_

        Returns:
            _type_: _description_
        """
        query_tokens = (
            select(UserAuthRefreshToken)
            .join(UserAuth)
            .where(UserAuth.user_id == user_id)
        )
        results = await self.session.exec(statement=query_tokens)
        tokens: Sequence[UserAuthRefreshToken] = results.all()
        for token in tokens:
            token.deactivated = True
            self.session.add(token)
        await self.session.commit()
