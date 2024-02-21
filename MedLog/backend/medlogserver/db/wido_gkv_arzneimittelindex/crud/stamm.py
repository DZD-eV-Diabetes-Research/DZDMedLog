from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, col
from sqlalchemy import func
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm import (
    Stamm,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()


class StammCRUD(DrugCRUDBase):
    async def count(self, current_version_only: bool = True) -> Sequence[Stamm]:
        query = select(func.count(Stamm.pzn))
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        print("results", results)
        return results.first()

    async def list(
        self, current_version_only: bool = True, pagination: PageParams = None
    ) -> Sequence[Stamm]:
        query = select(Stamm)
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)
        print("QUERY", query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get_multiple(
        self,
        pzns: List[str],
        current_version_only: bool = True,
        pagination: PageParams = None,
        keep_pzn_order: bool = True,
    ) -> Sequence[Stamm]:
        query = (
            select(Stamm)
            .where(col(Stamm.pzn).in_(pzns))
            .order_by(
                Stamm.pzn,  # Default order by ID to maintain database order
                (Stamm.pzn, pzns),
            )
        )
        log.debug(f"GET MULTIPLE QUERY: {query}")
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_pzn_order:
            db_order: List[Stamm] = results.all()
            new_order: List[Stamm] = []
            for pzn in pzns:
                db_order_item_index = next(
                    (i for i, obj in enumerate(db_order) if obj.pzn == pzn)
                )
                item = db_order.pop(db_order_item_index)
                new_order.append(item)
            return new_order
        return results.all()

    async def get(
        self,
        pzn: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Stamm]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Stamm).where(
            Stamm.pzn == pzn and Stamm.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        pzn: Stamm | None = results.one_or_none()
        if pzn is None and raise_exception_if_none:
            raise raise_exception_if_none
        return pzn

    async def create(
        self,
        stamm_create: Stamm,
        raise_exception_if_exists: Exception = None,
    ) -> Stamm:
        log.debug(f"Create stamm: {stamm_create}")
        existing_stamm = None
        if raise_exception_if_exists:
            existing_stamm = self.get(
                pzn=stamm_create.pzn,
                ai_version_id=stamm_create.ai_version_id,
            )

        if existing_stamm and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_stamm:
            return existing_stamm
        self.session.add(stamm_create)
        await self.session.commit()
        await self.session.refresh(stamm_create)
        return stamm_create

    async def create_bulk(
        self,
        objects: List[Stamm],
    ) -> Stamm:
        log.debug(f"Create bulk of stamm")
        for obj in objects:
            if not isinstance(obj, Stamm):
                raise ValueError(f"List item is not a Stamm instance:\n {objects}")
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        stamm_update: Stamm,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Stamm:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        stamm_stamm: str,
        ai_version_id: str | UUID = None,
    ) -> Stamm:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_stamm_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[StammCRUD, None]:
    yield StammCRUD(session=session)


get_stamm_crud_context = contextlib.asynccontextmanager(get_stamm_crud)
