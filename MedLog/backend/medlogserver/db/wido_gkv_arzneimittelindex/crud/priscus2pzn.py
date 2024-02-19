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
from medlogserver.db.wido_gkv_arzneimittelindex.model.priscus2pzn import (
    Priscus2PZN,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class Priscus2PZNCRUD(DrugCRUDBase):

    async def list(self, current_version_only: bool = True) -> Sequence[Priscus2PZN]:
        query = select(Priscus2PZN)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Priscus2PZN.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        return results.all()

    async def exists(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> bool:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Priscus2PZN).where(
            Priscus2PZN.pzn == pzn and Priscus2PZN.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: Priscus2PZN | None = results.one_or_none()
        if pzn is None:
            if raise_exception_if_none:
                raise_exception_if_none
            return False
        return True

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Priscus2PZN]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Priscus2PZN).where(
            Priscus2PZN.pzn == pzn and Priscus2PZN.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: Priscus2PZN | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        priscus2pzn_create: Priscus2PZN,
        raise_exception_if_exists: Exception = None,
    ) -> Priscus2PZN:
        log.debug(f"Create priscus2pzn: {priscus2pzn_create}")
        existing_priscus2pzn = None
        if raise_exception_if_exists:
            existing_priscus2pzn = self.get(
                pzn=priscus2pzn_create.pzn,
                ai_version_id=priscus2pzn_create.ai_version_id,
            )

        if existing_priscus2pzn and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_priscus2pzn:
            return existing_priscus2pzn
        self.session.add(priscus2pzn_create)
        await self.session.commit()
        await self.session.refresh(priscus2pzn_create)
        return priscus2pzn_create

    async def create_bulk(
        self,
        objects: List[Priscus2PZN],
    ) -> Priscus2PZN:
        log.debug(f"Create bulk of priscus2pzn")
        for obj in objects:
            if not isinstance(obj, Priscus2PZN):
                raise ValueError(
                    f"List item is not a Priscus2PZN instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        priscus2pzn_update: Priscus2PZN,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Priscus2PZN:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        priscus2pzn_priscus2pzn: str,
        ai_version_id: str | UUID = None,
    ) -> Priscus2PZN:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_priscus2pzn_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[Priscus2PZNCRUD, None]:
    yield Priscus2PZNCRUD(session=session)


get_priscus2pzn_crud_context = contextlib.asynccontextmanager(get_priscus2pzn_crud)
