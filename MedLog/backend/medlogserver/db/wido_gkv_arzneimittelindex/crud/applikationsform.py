from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
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
from medlogserver.db.wido_gkv_arzneimittelindex.model.applikationsform import (
    Applikationsform,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
    get_ai_data_version_crud,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class ApplikationsformCRUD(DrugCRUDBase):

    async def list(
        self, current_version_only: bool = True
    ) -> Sequence[Applikationsform]:
        query = select(Applikationsform)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version
            query = query.where(Applikationsform.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        appform: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Applikationsform]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Applikationsform).where(
            Applikationsform.appform == appform
            and Applikationsform.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        appform: Applikationsform | None = results.one_or_none()
        if appform is None and raise_exception_if_none:
            raise raise_exception_if_none
        return appform

    async def create(
        self,
        applikationsform_create: Applikationsform,
        raise_exception_if_exists: Exception = None,
    ) -> Applikationsform:
        log.debug(f"Create applikationsform: {applikationsform_create}")
        existing_appform = None
        if raise_exception_if_exists:
            existing_appform = self.get(
                appform=applikationsform_create.appform,
                ai_version_id=applikationsform_create.ai_version_id,
            )

        if existing_appform and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_appform:
            return existing_appform
        self.session.add(applikationsform_create)
        await self.session.commit()
        await self.session.refresh(applikationsform_create)
        return applikationsform_create

    async def create_bulk(
        self,
        objects: List[Applikationsform],
    ):
        log.debug(f"Create bulk of applikationsform")
        for obj in objects:
            if not isinstance(obj, Applikationsform):
                raise ValueError(
                    f"List item is not a Applikationsform instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        applikationsform_update: Applikationsform,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Applikationsform:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        applikationsform_appform: str,
        ai_version_id: str | UUID = None,
    ) -> Applikationsform:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_applikationsform_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[ApplikationsformCRUD, None]:
    yield ApplikationsformCRUD(session=session)


get_applikationsform_crud_context = contextlib.asynccontextmanager(
    get_applikationsform_crud
)
