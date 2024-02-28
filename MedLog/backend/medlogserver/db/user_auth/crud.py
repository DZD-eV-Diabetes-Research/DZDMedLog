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
from medlogserver.db.base import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.db.user.model import User
from medlogserver.db.user_auth.model import (
    UserAuth,
    UserAuthCreate,
    UserAuthUpdate,
    AllowedAuthSourceTypes,
    pwd_context,
)
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()


class UserAuthCRUD(CRUDBase[UserAuth, UserAuth, UserAuthCreate, UserAuthUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user_id(
        self,
        user_id: str | uuid.UUID,
        filter_auth_source_type: AllowedAuthSourceTypes = None,
        filter_oidc_provider_name: str = None,
        raise_exception_if_none: Exception = None,
        pagination: PageParams = None,
    ) -> Sequence[UserAuth]:
        query = select(UserAuth).where(UserAuth.user_id == user_id)
        if filter_auth_source_type:
            query = query.where(UserAuth.auth_source_type == filter_auth_source_type)
        if filter_oidc_provider_name:
            query = query.where(
                UserAuth.oidc_provider_name == filter_oidc_provider_name
            )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        user_auths: Sequence[UserAuth] = results.all()
        if user_auths is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user_auths

    async def list_by_user_name(
        self,
        user_name: str | uuid.UUID,
        filter_auth_source_type: AllowedAuthSourceTypes = None,
        filter_oidc_provider_name: str = None,
        raise_exception_if_none: Exception = None,
        pagination: PageParams = None,
    ) -> Sequence[UserAuth]:
        query = select(UserAuth).join(User).where(User.user_name == user_name)
        if filter_auth_source_type:
            query = query.where(UserAuth.auth_source_type == filter_auth_source_type)
        if filter_oidc_provider_name:
            query = query.where(
                UserAuth.oidc_provider_name == filter_oidc_provider_name
            )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        user: UserAuth | None = results.all()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_local_auth_source_by_user_id(
        self, user_id: str | uuid.UUID, raise_exception_if_none: Exception = None
    ) -> UserAuth | None:
        query = select(UserAuth).where(UserAuth.user_id == user_id)
        results = await self.session.exec(statement=query)
        user_auths: Sequence[UserAuth] | None = results.all()

        # for good measure we do a sanity check here. one user should only have one "local"-auth entry with a hashed password.
        if len(user_auths) > 1:
            # there are multiple local user auths. something is broken. Lets attach an uuid to the error, so we can identify it, if a user reports that.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details="Something went wrong. Please report this error. Error-id: f5d08a40-6d2e-442f-bd97-b0e3d0f9a2b7",
            )
        elif len(user_auths) == 0:
            if raise_exception_if_none:
                raise raise_exception_if_none
            return None
        user_auth = user_auths[0]
        return user_auth

    async def get_local_auth_source_by_user_name(
        self, user_name: str, raise_exception_if_none: Exception = None
    ) -> UserAuth | None:
        query = select(User).where(User.user_name == user_name)
        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if not user and raise_exception_if_none:
            raise raise_exception_if_none
        return await self.get_local_auth_source_by_user_id(user.id)

    async def create(self, user_auth_create: UserAuthCreate) -> UserAuth:
        password_hashed = None
        if user_auth_create.auth_source_type == AllowedAuthSourceTypes.local:
            if user_auth_create.password is None:
                raise ValueError("Password is not allowd to be empty for local users")
            password_hashed = pwd_context.hash(
                user_auth_create.password.get_secret_value()
            )

        user_vals = {}

        for k, v in user_auth_create.model_dump().items():
            log.info(f"{k} {v}")
            if k == "password":
                user_vals["password_hashed"] = password_hashed

            else:
                user_vals[k] = v

        log.debug(f"user_vals {user_vals}")
        user_auth = UserAuth(**user_vals)
        log.debug(user_auth)

        self.session.add(user_auth)
        await self.session.commit()
        await self.session.refresh(user_auth)
        return user_auth

    async def delete(
        self, id: str | uuid.UUID, raise_exception_if_not_exists=None
    ) -> None | Literal[True]:
        user_auth = select(UserAuth).where(UserAuth.id == id)
        if user_auth is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        else:
            query = delete(UserAuth).where(UserAuth.id == id)
            await self.session.exec(statement=query)
            await self.session.commit()
            return True

    async def update(
        self,
        user_auth_update: UserAuthUpdate,
        id: str | uuid.UUID = None,
    ) -> UserAuth:
        id = id if id is not None else user_auth_update.id
        if id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user_auth = select(UserAuth).where(UserAuth.id == id)
        password_hashed = pwd_context.hash(user_auth_update.password.get_secret_value())
        for k, v in user_auth_update.model_dump(exclude_unset=True).items():
            if k != "password":
                setattr(user_auth, "password_hashed", password_hashed)
            else:
                # this is unused code for now, as it is only possible to change the password. but maybe we add more attributes later to the UserAuthUpdate class
                setattr(user_auth, k, v)
        self.session.add(user_auth)
        await self.session.commit()
        await self.session.refresh(user_auth)
        return user_auth