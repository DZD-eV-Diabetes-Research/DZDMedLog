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
from medlogserver.db.wido_gkv_arzneimittelindex.model.hersteller import (
    Hersteller,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class HerstellerCRUD(DrugCRUDBase):

    async def list(self, current_version_only: bool = True) -> Sequence[Hersteller]:
        query = select(Hersteller)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Hersteller.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        herstellercode: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Hersteller]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Hersteller).where(
            Hersteller.herstellercode == herstellercode
            and Hersteller.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        herstellercode: Hersteller | None = results.one_or_none()
        if herstellercode is None and raise_exception_if_none:
            raise raise_exception_if_none
        return herstellercode

    async def create(
        self,
        hersteller_create: Hersteller,
        raise_exception_if_exists: Exception = None,
    ) -> Hersteller:
        log.debug(f"Create hersteller: {hersteller_create}")
        existing_hersteller = None
        if raise_exception_if_exists:
            existing_hersteller = self.get(
                herstellercode=hersteller_create.herstellercode,
                ai_version_id=hersteller_create.ai_version_id,
            )

        if existing_hersteller and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_hersteller:
            return existing_hersteller
        self.session.add(hersteller_create)
        await self.session.commit()
        await self.session.refresh(hersteller_create)
        return hersteller_create

    async def create_bulk(
        self,
        objects: List[Hersteller],
    ) -> Hersteller:
        log.debug(f"Create bulk of hersteller")
        for obj in objects:
            if not isinstance(obj, Hersteller):
                raise ValueError(f"List item is not a Hersteller instance:\n {objects}")
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        hersteller_update: Hersteller,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Hersteller:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        hersteller_hersteller: str,
        ai_version_id: str | UUID = None,
    ) -> Hersteller:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_hersteller_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[HerstellerCRUD, None]:
    yield HerstellerCRUD(session=session)


get_hersteller_crud_context = contextlib.asynccontextmanager(get_hersteller_crud)
