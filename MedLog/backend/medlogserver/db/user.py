from typing import AsyncGenerator, List, Optional, Literal, Sequence
from pydantic import SecretStr
from fastapi import Depends
import contextlib
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.user_auth import UserAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class UserBase(Base, table=False):
    email: str = Field(default=None, index=True)
    display_name: str = Field(default=None, max_length=128)
    roles: List[str] = Field(default=[], sa_column=Column(JSON))
    disabled: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)


class User(UserBase, BaseTable, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    user_name: str = Field(default=None, index=True, unique=True)


class UserUpdate(UserBase, table=False):
    id: Optional[uuid.UUID] = Field(default=None)


class UserCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        user_id: str | UUID,
        show_disabled: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[User]:
        if show_disabled:
            query = select(User).where(User.id == user_id)
        else:
            query = select(User).where(User.id == user_id and User.disabled == False)
        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_by_user_name(
        self,
        user_name: str | UUID,
        show_disabled: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[User]:
        if show_disabled:
            query = select(User).where(User.user_name == user_name)
        else:
            query = select(User).where(
                User.user_name == user_name and User.disabled == False
            )
        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def create(
        self,
        user: User,
        exists_ok: bool = False,
        raise_exception_if_exists: Exception = None,
    ) -> User:
        existing_user: User = await self.get_by_user_name(
            user.user_name, show_disabled=True
        )
        if existing_user is not None and not exists_ok:
            raise raise_exception_if_exists if raise_exception_if_exists else ValueError(
                f"User with user_name {user.user_name} already exists"
            )
        if user.display_name is None:
            user.display_name = user.user_name
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def disable(
        self,
        user_id: str | UUID,
        raise_exception_if_not_exists=None,
        raise_exception_if_allready_disabled=None,
    ) -> bool:
        if user_id is None:
            raise ValueError("No user_id provided")
        user = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_disabled=True,
        )
        if user.disabled and raise_exception_if_allready_disabled:
            raise raise_exception_if_allready_disabled
        user.disabled = True
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        # for good measure disable all refresh tokens as well
        # TODO: this generated a circular import we need to seperate model and crud classes
        # UserAuthRefreshTokenCRUD(self.session).disable_by_user_id(user_id=user_id)
        return user

    async def update(
        self,
        user_update: UserUpdate,
        user_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> User:
        user_id = user_id if user_id else user_update.id
        if user_id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_disabled=True,
        )
        for k, v in user_update.model_dump(exclude_unset=True).items():
            if k in UserUpdate.model_fields.keys():
                setattr(user, k, v)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(
        self,
        user_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> User:
        user = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_disabled=True,
        )
        if user is not None:
            delete(user).where(User.pk == user_id)
        return True


async def get_users_crud(
    session: AsyncSession = Depends(get_async_session),
) -> UserCRUD:
    yield UserCRUD(session=session)


get_users_crud_context = contextlib.asynccontextmanager(get_users_crud)
