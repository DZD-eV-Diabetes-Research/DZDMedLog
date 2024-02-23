from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.enum_preisart import (
    Preisart,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class PreisartCRUD(DrugCRUDBase):
    _table_ = Preisart
    _ai_versionless_table_: bool = True

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def get(
        self,
        preisart: str,
    ) -> Optional[Preisart]:
        query = select(Preisart).where(Preisart.preisart == preisart)
        results = await self.session.exec(statement=query)
        preisart: Preisart | None = results.one_or_none()
        return preisart

    async def create(
        self,
        preisart_create: Preisart,
        raise_exception_if_exists: Exception = None,
    ) -> Preisart:
        existing_preisart = await self.get(
            preisart=preisart_create.preisart,
        )
        if raise_exception_if_exists and existing_preisart:
            raise raise_exception_if_exists
        elif existing_preisart:
            return existing_preisart
        self.session.add(preisart_create)
        await self.session.commit()
        await self.session.refresh(preisart_create)
        return preisart_create

    async def create_bulk(
        self,
        objects: List[Preisart],
    ) -> Preisart:
        log.debug(f"Create bulk of enum preisart")
        for obj in objects:
            if not isinstance(obj, Preisart):
                raise ValueError(f"List item is not a Preisart instance:\n {objects}")
            await self.create(obj)

    async def update(
        self,
        preisart_update: Preisart,
        raise_exception_if_not_exists=None,
    ) -> Preisart:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        preisart_preisart: str,
    ) -> Preisart:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_preisart_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[PreisartCRUD, None]:
    yield PreisartCRUD(session=session)


get_preisart_crud_context = contextlib.asynccontextmanager(get_preisart_crud)
