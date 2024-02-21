from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from sqlalchemy.sql.operators import is_not, is_
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)

log = get_logger()
config = Config()


class AiDataVersionCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        include_deactivated: bool = False,
        include_incompleted: bool = False,
        filter_by_datenstand: str = None,
        filter_by_dateiversion: str = None,
    ) -> Sequence[AiDataVersion]:
        query = select(AiDataVersion)
        if not include_deactivated:
            query = query.where(AiDataVersion.deactivated == False)
        if not include_incompleted:
            query = query.where(is_not(AiDataVersion.import_completed_at, None))
        if filter_by_datenstand:
            query = query.where(AiDataVersion.datenstand == filter_by_datenstand)
        if filter_by_dateiversion:
            query = query.where(AiDataVersion.dateiversion == filter_by_dateiversion)

        query = query.order_by(desc(AiDataVersion.datenstand))
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[AiDataVersion]:
        query = select(AiDataVersion).where(AiDataVersion.id == id)

        results = await self.session.exec(statement=query)
        vers: AiDataVersion | None = results.one_or_none()
        if vers is None and raise_exception_if_none:
            raise raise_exception_if_none
        return vers

    async def get_by_datenstand_and_dateiversion(
        self,
        datenstand: str,
        dateiversion: str,
        raise_exception_if_none: Exception = None,
    ) -> Optional[AiDataVersion]:

        query = select(AiDataVersion).where(
            AiDataVersion.datenstand == datenstand
            and AiDataVersion.dateiversion == dateiversion
        )

        results = await self.session.exec(statement=query)
        vers: AiDataVersion | None = results.one_or_none()
        if vers is None and raise_exception_if_none:
            raise raise_exception_if_none
        return vers

    async def get_current(self, none_is_ok: bool = False) -> AiDataVersion:
        query = (
            select(AiDataVersion)
            .where(AiDataVersion.deactivated == False)
            .where(is_not(AiDataVersion.import_completed_at, None))
            .order_by(desc(AiDataVersion.datenstand))
        )
        results = await self.session.exec(statement=query)
        res = results.one_or_none()
        if res is None and not none_is_ok:
            raise ValueError(
                "Could not determine a GKV WiDo Arzneimittel index data version. Maybe no Arzneimittel index was imported yet or there is a bug."
            )
        return res

    async def create(
        self,
        ai_data_version_create: AiDataVersion,
        raise_exception_if_exists: Exception = None,
    ) -> AiDataVersion:
        log.debug(f"Create ai_data_version: {ai_data_version_create}")

        existing_ai_data_version: Sequence[AiDataVersion] = await self.list(
            include_deactivated=True,
            include_incompleted=True,
            filter_by_dateiversion=ai_data_version_create.dateiversion,
            filter_by_datenstand=ai_data_version_create.datenstand,
        )
        if existing_ai_data_version and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_ai_data_version:
            return existing_ai_data_version[0]
        self.session.add(ai_data_version_create)
        await self.session.commit()
        await self.session.refresh(ai_data_version_create)
        return ai_data_version_create

    async def create_bulk(
        self,
        objects: List[AiDataVersion],
    ):
        log.debug(f"Create bulk ai_data_version")
        for obj in objects:
            if not isinstance(obj, AiDataVersion):
                raise ValueError(
                    f"List item is not a AiDataVersion instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def disable(
        self,
        ai_data_version_id: str | UUID,
        raise_exception_if_not_exists=None,
        raise_exception_if_allready_deactivated=None,
    ) -> AiDataVersion:
        ai_data_version: AiDataVersion = await self.get(
            ai_data_version_id=ai_data_version_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        if ai_data_version.deactivated and raise_exception_if_allready_deactivated:
            raise raise_exception_if_allready_deactivated
        ai_data_version.deactivated = True
        self.session.add(ai_data_version)
        await self.session.commit()
        await self.session.refresh(ai_data_version)
        return ai_data_version

    async def update(
        self,
        ai_data_version_update: AiDataVersion,
        ai_data_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> AiDataVersion:
        obj_id = ai_data_version_id if ai_data_version_id else ai_data_version_update.id
        ai_data_version_from_db = await self.get(
            id=obj_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        for k, v in ai_data_version_update.model_dump(exclude_unset=True).items():
            if k in AiDataVersion.model_fields.keys():
                setattr(ai_data_version_from_db, k, v)
        self.session.add(ai_data_version_from_db)
        await self.session.commit()
        await self.session.refresh(ai_data_version_from_db)
        return ai_data_version_from_db

    async def delete(
        self,
        ai_data_version_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> AiDataVersion:
        obj = await self.get(
            ai_data_version_id=ai_data_version_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        if obj is not None:
            delete(obj).where(AiDataVersion.id == ai_data_version_id)
        return True


async def get_ai_data_version_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[AiDataVersionCRUD, None]:
    yield AiDataVersionCRUD(session=session)


get_ai_data_version_crud_context = contextlib.asynccontextmanager(
    get_ai_data_version_crud
)
