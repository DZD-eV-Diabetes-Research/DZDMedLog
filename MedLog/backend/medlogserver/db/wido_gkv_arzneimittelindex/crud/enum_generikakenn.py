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
from medlogserver.db.wido_gkv_arzneimittelindex.model.enum_generikakenn import (
    Generikakennung,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class GenerikakennungCRUD:

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def list(self) -> Sequence[Generikakennung]:
        query = select(Generikakennung)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        generikakenn: int,
    ) -> Optional[Generikakennung]:
        query = select(Generikakennung).where(
            Generikakennung.generikakenn == generikakenn
        )
        results = await self.session.exec(statement=query)
        generikakenn: Generikakennung | None = results.one_or_none()
        return generikakenn

    async def create(
        self,
        generikakenn_create: Generikakennung,
        raise_exception_if_exists: Exception = None,
    ) -> Generikakennung:
        existing_generikakenn = await self.get(
            generikakenn=generikakenn_create.generikakenn,
        )
        if raise_exception_if_exists and existing_generikakenn:
            raise raise_exception_if_exists
        elif existing_generikakenn:
            return existing_generikakenn
        self.session.add(generikakenn_create)
        await self.session.commit()
        await self.session.refresh(generikakenn_create)
        return generikakenn_create

    async def create_bulk(
        self,
        objects: List[Generikakennung],
    ) -> Generikakennung:
        log.debug(f"Create bulk of enum generikakenn")
        for obj in objects:
            if not isinstance(obj, Generikakennung):
                raise ValueError(
                    f"List item is not a Generikakennung instance:\n {objects}"
                )
            await self.create(obj)

    async def update(
        self,
        generikakenn_update: Generikakennung,
        raise_exception_if_not_exists=None,
    ) -> Generikakennung:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        generikakenn_generikakenn: str,
    ) -> Generikakennung:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_generikakenn_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[GenerikakennungCRUD, None]:
    yield GenerikakennungCRUD(session=session)


get_generikakenn_crud_context = contextlib.asynccontextmanager(get_generikakenn_crud)
