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
from medlogserver.db.wido_gkv_arzneimittelindex.model.atc_amtlich import (
    ATCAmtlich,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class ATCAmtlichCRUD(DrugCRUDBase):
    _table_ = ATCAmtlich

    async def get(
        self,
        atccode: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[ATCAmtlich]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(ATCAmtlich).where(
            ATCAmtlich.atccode == atccode and ATCAmtlich.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        atccode: ATCAmtlich | None = results.one_or_none()
        if atccode is None and raise_exception_if_none:
            raise raise_exception_if_none
        return atccode

    async def create(
        self,
        atc_amtlich_create: ATCAmtlich,
        raise_exception_if_exists: Exception = None,
    ) -> ATCAmtlich:
        log.debug(f"Create atc_amtlich: {atc_amtlich_create}")
        existing_atccode = None
        if raise_exception_if_exists:
            existing_atccode = self.get(
                atccode=atc_amtlich_create.atccode,
                ai_version_id=atc_amtlich_create.ai_version_id,
            )

        if existing_atccode and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_atccode:
            return existing_atccode
        self.session.add(atc_amtlich_create)
        await self.session.commit()
        await self.session.refresh(atc_amtlich_create)
        return atc_amtlich_create

    async def create_bulk(
        self,
        objects: List[ATCAmtlich],
    ) -> ATCAmtlich:
        log.debug(f"Create bulk of atc_amtlich")
        for obj in objects:
            if not isinstance(obj, ATCAmtlich):
                raise ValueError(f"List item is not a ATCAmtlich instance:\n {objects}")
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        atc_amtlich_update: ATCAmtlich,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> ATCAmtlich:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        atc_amtlich_atccode: str,
        ai_version_id: str | UUID = None,
    ) -> ATCAmtlich:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_atc_amtlich_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[ATCAmtlichCRUD, None]:
    yield ATCAmtlichCRUD(session=session)


get_atc_amtlich_crud_context = contextlib.asynccontextmanager(get_atc_amtlich_crud)
