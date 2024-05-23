from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from sqlalchemy.sql.operators import is_not, is_
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db._base_crud import create_crud_base

log = get_logger()
config = Config()


class AiDataVersionCRUD(
    create_crud_base(
        table_model=AiDataVersion,
        read_model=AiDataVersion,
        create_model=AiDataVersion,
        update_model=AiDataVersion,
    )
):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        include_deactivated: bool = False,
        include_incompleted: bool = False,
        filter_datenstand: str = None,
        filter_dateiversion: str = None,
    ) -> Sequence[AiDataVersion]:
        query = select(AiDataVersion)
        if not include_deactivated:
            query = query.where(AiDataVersion.deactivated == False)
        if not include_incompleted:
            query = query.where(is_not(AiDataVersion.import_completed_at, None))
        if filter_datenstand:
            query = query.where(AiDataVersion.datenstand == filter_datenstand)
        if filter_dateiversion:
            query = query.where(AiDataVersion.dateiversion == filter_dateiversion)
        query = query.where(AiDataVersion.dateiversion != "user-custom-drugs")

        query = query.order_by(desc(AiDataVersion.datenstand))
        results = await self.session.exec(statement=query)
        return results.all()

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
            .where(AiDataVersion.dateiversion != "user-custom-drugs")
            .order_by(desc(AiDataVersion.datenstand))
        )
        results = await self.session.exec(statement=query)
        res = results.one_or_none()
        if res is None and not none_is_ok:
            raise ValueError(
                "Could not determine a GKV WiDo Arzneimittel index data version. Maybe no Arzneimittel index was imported yet or there is a bug."
            )
        return res

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
