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
from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm_aenderungen import (
    StammAenderungen,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class StammAenderungenCRUD(DrugCRUDBase):

    async def list(
        self, current_version_only: bool = True
    ) -> Sequence[StammAenderungen]:
        query = select(StammAenderungen)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(StammAenderungen.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[StammAenderungen]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(StammAenderungen).where(
            StammAenderungen.pzn == pzn
            and StammAenderungen.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: StammAenderungen | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        stamm_aenderungen_create: StammAenderungen,
        raise_exception_if_exists: Exception = None,
    ) -> StammAenderungen:
        log.debug(f"Create stamm_aenderungen: {stamm_aenderungen_create}")
        existing_stamm_aenderungen = None
        if raise_exception_if_exists:
            existing_stamm_aenderungen = self.get(
                pzn=stamm_aenderungen_create.pzn,
                ai_version_id=stamm_aenderungen_create.ai_version_id,
            )

        if existing_stamm_aenderungen and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_stamm_aenderungen:
            return existing_stamm_aenderungen
        self.session.add(stamm_aenderungen_create)
        await self.session.commit()
        await self.session.refresh(stamm_aenderungen_create)
        return stamm_aenderungen_create

    async def create_bulk(
        self,
        objects: List[StammAenderungen],
    ) -> StammAenderungen:
        log.debug(f"Create bulk of stamm_aenderungen")
        for obj in objects:
            if not isinstance(obj, StammAenderungen):
                raise ValueError(
                    f"List item is not a StammAenderungen instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        stamm_aenderungen_update: StammAenderungen,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> StammAenderungen:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        stamm_aenderungen_stamm_aenderungen: str,
        ai_version_id: str | UUID = None,
    ) -> StammAenderungen:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_stamm_aenderungen_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[StammAenderungenCRUD, None]:
    yield StammAenderungenCRUD(session=session)


get_stamm_aenderungen_crud_context = contextlib.asynccontextmanager(
    get_stamm_aenderungen_crud
)
