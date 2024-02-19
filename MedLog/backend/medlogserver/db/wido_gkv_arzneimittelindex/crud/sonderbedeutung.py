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
from medlogserver.db.wido_gkv_arzneimittelindex.model.sonderbedeutung import (
    SondercodeBedeutung,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class SondercodeBedeutungCRUD(DrugCRUDBase):

    async def list(
        self, current_version_only: bool = True
    ) -> Sequence[SondercodeBedeutung]:
        query = select(SondercodeBedeutung)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(
                SondercodeBedeutung.ai_version_id == current_ai_version.id
            )

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        sondercode: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[SondercodeBedeutung]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(SondercodeBedeutung).where(
            SondercodeBedeutung.sonder_atc_gruppe == sondercode
            and SondercodeBedeutung.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        sondercode: SondercodeBedeutung | None = results.one_or_none()
        if sondercode is None and raise_exception_if_none:
            raise raise_exception_if_none
        return sondercode

    async def create(
        self,
        sonderbedeutungcode_create: SondercodeBedeutung,
        raise_exception_if_exists: Exception = None,
    ) -> SondercodeBedeutung:
        log.debug(f"Create sonderbedeutung: {sonderbedeutungcode_create}")
        existing_sonderbedeutungcode = None
        if raise_exception_if_exists:
            existing_sonderbedeutungcode = self.get(
                sondercode=sonderbedeutungcode_create.sonder_atc_gruppe,
                ai_version_id=sonderbedeutungcode_create.ai_version_id,
            )

        if existing_sonderbedeutungcode and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_sonderbedeutungcode:
            return existing_sonderbedeutungcode
        self.session.add(sonderbedeutungcode_create)
        await self.session.commit()
        await self.session.refresh(sonderbedeutungcode_create)
        return sonderbedeutungcode_create

    async def create_bulk(
        self,
        objects: List[SondercodeBedeutung],
    ) -> SondercodeBedeutung:
        log.debug(f"Create bulk of sonderbedeutung")
        for obj in objects:
            if not isinstance(obj, SondercodeBedeutung):
                raise ValueError(
                    f"List item is not a SondercodeBedeutung instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        sonderbedeutungcode_update: SondercodeBedeutung,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> SondercodeBedeutung:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        sonderbedeutungcode_sondercode: str,
        ai_version_id: str | UUID = None,
    ) -> SondercodeBedeutung:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_sonderbedeutungcode_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SondercodeBedeutungCRUD, None]:
    yield SondercodeBedeutungCRUD(session=session)


get_sonderbedeutungcode_crud_context = contextlib.asynccontextmanager(
    get_sonderbedeutungcode_crud
)
