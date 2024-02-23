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
from medlogserver.db.wido_gkv_arzneimittelindex.model.sonder import (
    Sondercodes,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class SondercodesCRUD(DrugCRUDBase):
    _table_ = Sondercodes

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Sondercodes]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Sondercodes).where(
            Sondercodes.pzn == pzn and Sondercodes.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: Sondercodes | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        sondercode_create: Sondercodes,
        raise_exception_if_exists: Exception = None,
    ) -> Sondercodes:
        log.debug(f"Create sonder: {sondercode_create}")
        existing_sondercode = None
        if raise_exception_if_exists:
            existing_sondercode = self.get(
                pzn=sondercode_create.pzn,
                ai_version_id=sondercode_create.ai_version_id,
            )

        if existing_sondercode and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_sondercode:
            return existing_sondercode
        self.session.add(sondercode_create)
        await self.session.commit()
        await self.session.refresh(sondercode_create)
        return sondercode_create

    async def create_bulk(
        self,
        objects: List[Sondercodes],
    ) -> Sondercodes:
        log.debug(f"Create bulk of sonder")
        for obj in objects:
            if not isinstance(obj, Sondercodes):
                raise ValueError(
                    f"List item is not a Sondercodes instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        sondercode_update: Sondercodes,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Sondercodes:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        sondercode_pzn: str,
        ai_version_id: str | UUID = None,
    ) -> Sondercodes:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_sondercode_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SondercodesCRUD, None]:
    yield SondercodesCRUD(session=session)


get_sondercode_crud_context = contextlib.asynccontextmanager(get_sondercode_crud)
