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
from medlogserver.db.wido_gkv_arzneimittelindex.model.ergaenzung_amtlich import (
    ATCErgaenzungAmtlich,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class ATCErgaenzungAmtlichCRUD(DrugCRUDBase):

    async def list(
        self, current_version_only: bool = True
    ) -> Sequence[ATCErgaenzungAmtlich]:
        query = select(ATCErgaenzungAmtlich)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version
            query = query.where(
                ATCErgaenzungAmtlich.ai_version_id == current_ai_version.id
            )

        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[ATCErgaenzungAmtlich]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(ATCErgaenzungAmtlich).where(
            ATCErgaenzungAmtlich.pzn == pzn
            and ATCErgaenzungAmtlich.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: ATCErgaenzungAmtlich | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        ergaenzung_amtlich_create: ATCErgaenzungAmtlich,
        raise_exception_if_exists: Exception = None,
    ) -> ATCErgaenzungAmtlich:
        log.debug(f"Create ergaenzung_amtlich: {ergaenzung_amtlich_create}")
        existing_ergaenzung_amtlich = None
        if raise_exception_if_exists:
            existing_ergaenzung_amtlich = self.get(
                pzn=ergaenzung_amtlich_create.pzn,
                ai_version_id=ergaenzung_amtlich_create.ai_version_id,
            )

        if existing_ergaenzung_amtlich and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_ergaenzung_amtlich:
            return existing_ergaenzung_amtlich
        self.session.add(ergaenzung_amtlich_create)
        await self.session.commit()
        await self.session.refresh(ergaenzung_amtlich_create)
        return ergaenzung_amtlich_create

    async def create_bulk(
        self,
        objects: List[ATCErgaenzungAmtlich],
    ) -> ATCErgaenzungAmtlich:
        log.debug(f"Create bulk of ergaenzung_amtlich")
        for obj in objects:
            if not isinstance(obj, ATCErgaenzungAmtlich):
                raise ValueError(
                    f"List item is not a ATCErgaenzungAmtlich instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        ergaenzung_amtlich_update: ATCErgaenzungAmtlich,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> ATCErgaenzungAmtlich:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        ergaenzung_amtlich_ergaenzung_amtlich: str,
        ai_version_id: str | UUID = None,
    ) -> ATCErgaenzungAmtlich:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_ergaenzung_amtlich_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[ATCErgaenzungAmtlichCRUD, None]:
    yield ATCErgaenzungAmtlichCRUD(session=session)


get_ergaenzung_amtlich_crud_context = contextlib.asynccontextmanager(
    get_ergaenzung_amtlich_crud
)
