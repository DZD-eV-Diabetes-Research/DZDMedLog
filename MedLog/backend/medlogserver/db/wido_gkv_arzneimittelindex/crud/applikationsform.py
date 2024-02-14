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

log = get_logger()
config = Config()


class ApplikationsformCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def _get_current_ai_version(self):
        if self._current_ai_version is None:

            ai_version_crud: AiDataVersionCRUD = await get_ai_data_version_crud(
                self.session
            )
            self._current_ai_version = await ai_version_crud.get_current()

        return self._current_ai_version

    async def list(
        self, current_version_only: bool = True
    ) -> Sequence[Applikationsform]:
        query = select(Applikationsform)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version
            query = query.where(
                Applikationsform.datenstand == current_ai_version.datenstand
                and Applikationsform.dateiversion == current_ai_version.dateiversion
            )

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        appform: str,
        dateiversion: str = None,
        datenstand: str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Applikationsform]:
        current_ai_version = await self._get_current_ai_version()
        if dateiversion is None:
            dateiversion == current_ai_version.dateiversion
        if datenstand is None:
            datenstand == current_ai_version.datenstand

        query = select(Applikationsform).where(
            Applikationsform.appform == appform
            and Applikationsform.datenstand == datenstand
            and Applikationsform.dateiversion == dateiversion
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
                datenstand=applikationsform_create.datenstand,
                dateiversion=applikationsform_create.dateiversion,
            )

        if existing_appform and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_appform:
            return existing_appform
        self.session.add(applikationsform_create)
        await self.session.commit()
        await self.session.refresh(applikationsform_create)
        return applikationsform_create

    async def update(
        self,
        applikationsform_update: Applikationsform,
        applikationsform_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> Applikationsform:
        existing_appform = self.get(
            appform=applikationsform_create.appform,
            datenstand=applikationsform_create.datenstand,
            dateiversion=applikationsform_create.dateiversion,
        )

        applikationsform_from_db = await self.get(
            applikationsform_id=applikationsform_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        for k, v in applikationsform_update.model_dump(exclude_unset=True).items():
            if k in Applikationsform.model_fields.keys():
                setattr(applikationsform_from_db, k, v)
        self.session.add(applikationsform_from_db)
        await self.session.commit()
        await self.session.refresh(applikationsform_from_db)
        return applikationsform_from_db

    async def delete(
        self,
        applikationsform_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> Applikationsform:
        user = await self.get(
            applikationsform_id=applikationsform_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if user is not None:
            delete(user).where(Applikationsform.id == applikationsform_id)
        return True


async def get_applikationsform_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[ApplikationsformCRUD, None]:
    yield ApplikationsformCRUD(session=session)


get_applikationsform_crud_context = contextlib.asynccontextmanager(
    get_applikationsform_crud
)
