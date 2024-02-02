from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
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


class EventBase(Base, table=False):
    name: str = Field(
        default=None,
        index=True,
        max_length=32,
        schema_extra={"examples": ["visit01", "TI12"]},
    )
    completed: bool = Field(
        default=False,
        description="Is the event completed. E.g. All study participants have been interviewed.",
    )


class Event(EventBase, BaseTable, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class InterviewCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[Drug]:
        query = select(Drug)
        if not show_deactivated:
            query = select(Drug).where(Drug.deactivated == False)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        user_id: str | UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[User]:
        query = select(User).where(User.id == user_id)
        if not show_deactivated:
            query.where(User.deactivated == False)

        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_by_user_name(
        self,
        user_name: str | UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[User]:
        if show_deactivated:
            query = select(User).where(User.user_name == user_name)
        else:
            query = select(User).where(
                User.user_name == user_name and User.deactivated == False
            )
        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def create(
        self,
        user: UserCreate | User,
        exists_ok: bool = False,
        raise_exception_if_exists: Exception = None,
    ) -> User:
        if type(user) is UserCreate:
            user: User = User.model_validate(user)
        log.debug(f"Create user: {user}")
        existing_user: User = await self.get_by_user_name(
            user.user_name, show_deactivated=True
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
        raise_exception_if_allready_deactivated=None,
    ) -> bool:
        if user_id is None:
            raise ValueError("No user_id provided")
        user = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if user.deactivated and raise_exception_if_allready_deactivated:
            raise raise_exception_if_allready_deactivated
        user.deactivated = True
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        # for good measure disable all refresh tokens as well
        # TODO: this generated a circular import we need to seperate model and crud classes
        # UserAuthRefreshTokenCRUD(self.session).disable_by_user_id(user_id=user_id)
        return user

    async def update(
        self,
        user_update: UserUpdate | UserUpdateByUser | UserUpdateByAdmin,
        user_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> User:
        user_id = user_id if user_id else user_update.id
        if user_id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user_from_db = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        for k, v in user_update.model_dump(exclude_unset=True).items():
            if k in UserUpdate.model_fields.keys():
                setattr(user_from_db, k, v)
        self.session.add(user_from_db)
        await self.session.commit()
        await self.session.refresh(user_from_db)
        return user_from_db

    async def delete(
        self,
        user_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> User:
        user = await self.get(
            user_id=user_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if user is not None:
            delete(user).where(User.pk == user_id)
        return True


async def get_user_crud(
    session: AsyncSession = Depends(get_async_session),
) -> UserCRUD:
    yield UserCRUD(session=session)


get_users_crud_context = contextlib.asynccontextmanager(get_user_crud)
