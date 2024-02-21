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
from medlogserver.db.wido_gkv_arzneimittelindex.model.enum_biosimilar import (
    Biosimilar,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class BiosimilarCRUD:

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def list(self) -> Sequence[Biosimilar]:
        query = select(Biosimilar)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        biosimilar: str,
    ) -> Optional[Biosimilar]:
        query = select(Biosimilar).where(Biosimilar.biosimilar == biosimilar)
        results = await self.session.exec(statement=query)
        biosimilar: Biosimilar | None = results.one_or_none()
        return biosimilar

    async def create(
        self,
        biosimilar_create: Biosimilar,
        raise_exception_if_exists: Exception = None,
    ) -> Biosimilar:
        existing_biosimilar = await self.get(
            biosimilar=biosimilar_create.biosimilar,
        )
        if raise_exception_if_exists and existing_biosimilar:
            raise raise_exception_if_exists
        elif existing_biosimilar:
            return existing_biosimilar
        self.session.add(biosimilar_create)
        await self.session.commit()
        await self.session.refresh(biosimilar_create)
        return biosimilar_create

    async def create_bulk(
        self,
        objects: List[Biosimilar],
    ) -> Biosimilar:
        log.debug(f"Create bulk of enum biosimilar")
        for obj in objects:
            if not isinstance(obj, Biosimilar):
                raise ValueError(f"List item is not a Biosimilar instance:\n {objects}")
            await self.create(obj)

    async def update(
        self,
        biosimilar_update: Biosimilar,
        raise_exception_if_not_exists=None,
    ) -> Biosimilar:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        biosimilar_biosimilar: str,
    ) -> Biosimilar:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_biosimilar_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[BiosimilarCRUD, None]:
    yield BiosimilarCRUD(session=session)


get_biosimilar_crud_context = contextlib.asynccontextmanager(get_biosimilar_crud)
