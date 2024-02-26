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
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.recycle import (
    RecycledPZN,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class RecycledPZNCRUD(DrugCRUDBase):
    _table_ = RecycledPZN

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[RecycledPZN]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(RecycledPZN).where(
            RecycledPZN.recycle == pzn and RecycledPZN.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: RecycledPZN | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        recycle_create: RecycledPZN,
        raise_exception_if_exists: Exception = None,
    ) -> RecycledPZN:
        log.debug(f"Create recycle: {recycle_create}")
        existing_recycle = None
        if raise_exception_if_exists:
            existing_recycle = self.get(
                pzn=recycle_create.recycle,
                ai_version_id=recycle_create.ai_version_id,
            )

        if existing_recycle and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_recycle:
            return existing_recycle
        self.session.add(recycle_create)
        await self.session.commit()
        await self.session.refresh(recycle_create)
        return recycle_create

    async def create_bulk(
        self,
        objects: List[RecycledPZN],
    ) -> RecycledPZN:
        log.debug(f"Create bulk of recycle")
        for obj in objects:
            if not isinstance(obj, RecycledPZN):
                raise ValueError(
                    f"List item is not a RecycledPZN instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        recycle_update: RecycledPZN,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> RecycledPZN:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        recycle_recycle: str,
        ai_version_id: str | UUID = None,
    ) -> RecycledPZN:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_recycle_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[RecycledPZNCRUD, None]:
    yield RecycledPZNCRUD(session=session)


get_recycle_crud_context = contextlib.asynccontextmanager(get_recycle_crud)
