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
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.enum_apofplicht import (
    ApoPflicht,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class ApoPflichtCRUD(DrugCRUDBase):
    _table_ = ApoPflicht
    _ai_versionless_table_: bool = True

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def get(
        self,
        apopflicht: int,
    ) -> Optional[ApoPflicht]:
        query = select(ApoPflicht).where(ApoPflicht.apopflicht == apopflicht)
        results = await self.session.exec(statement=query)
        apopflicht: ApoPflicht | None = results.one_or_none()
        return apopflicht

    async def create(
        self,
        apopflicht_create: ApoPflicht,
        raise_exception_if_exists: Exception = None,
    ) -> ApoPflicht:
        existing_apopflicht = await self.get(
            apopflicht=apopflicht_create.apopflicht,
        )
        if raise_exception_if_exists and existing_apopflicht:
            raise raise_exception_if_exists
        elif existing_apopflicht:
            return existing_apopflicht
        self.session.add(apopflicht_create)
        await self.session.commit()
        await self.session.refresh(apopflicht_create)
        return apopflicht_create

    async def create_bulk(
        self,
        objects: List[ApoPflicht],
    ) -> ApoPflicht:
        log.debug(f"Create bulk of enum apopflicht")
        for obj in objects:
            if not isinstance(obj, ApoPflicht):
                raise ValueError(f"List item is not a ApoPflicht instance:\n {objects}")
            await self.create(obj)

    async def update(
        self,
        apopflicht_update: ApoPflicht,
        raise_exception_if_not_exists=None,
    ) -> ApoPflicht:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        apopflicht_apopflicht: str,
    ) -> ApoPflicht:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_apopflicht_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[ApoPflichtCRUD, None]:
    yield ApoPflichtCRUD(session=session)


get_apopflicht_crud_context = contextlib.asynccontextmanager(get_apopflicht_crud)
