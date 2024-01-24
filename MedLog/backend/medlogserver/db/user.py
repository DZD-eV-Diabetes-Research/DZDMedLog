from typing import AsyncGenerator, List, Optional, Literal
from pydantic import SecretStr, Json
from fastapi import Depends
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable, AsyncSession, get_session

from sqlmodel import Field, select, delete
from uuid import UUID

log = get_logger()
config = Config()


# User Models and Table
class UserBase(BaseTable, table=False):
    email: str = Field(default=None, index=True)
    display_name: str = Field(default=None, max_length=128)
    roles: List[str] = Field(default=[])
    disabled: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)


class User(UserBase, table=True):
    __tablename__ = "user"
    username: str = Field(default=None, index=True, unique=True)


class UserUpdate(UserBase, table=False):
    pass


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

    async def get_by_username(
        self,
        username: str | UUID,
        show_disabled: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[User]:
        if show_disabled:
            query = select(User).where(User.username == username)
        else:
            query = select(User).where(
                User.username == username and User.disabled == False
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
        existing_user = await self.get_by_username(user.username, show_disabled=True)
        if existing_user is not None and not exists_ok:
            raise raise_exception_if_exists if raise_exception_if_exists else ValueError(
                f"User with username {user.username} already exists"
            )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(
        self,
        user_update: UserUpdate,
        user_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> User:
        user_id = user_id if user_id is not None else user_update.id
        if user_id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user = await self.get(
            user_id=user_update.id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_disabled=True,
        )
        for k, v in user_update.model_dump(exclude_unset=True).items():
            setattr(user, k, v)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return User

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
            delete(user).where(User.id == user_id)
        return True


async def get_users_crud(
    session: AsyncSession = Depends(get_session),
) -> UserCRUD:
    return UserCRUD(session=session)
