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
from medlogserver.db.wido_gkv_arzneimittelindex.model.normpackungsgroessen import (
    Normpackungsgroessen,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()

from sqlmodel import func


class NormpackungsgroessenCRUD(DrugCRUDBase):
    _table_ = Normpackungsgroessen

    async def get(
        self,
        zuzahlstufe: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Normpackungsgroessen]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Normpackungsgroessen).where(
            Normpackungsgroessen.zuzahlstufe == zuzahlstufe
            and Normpackungsgroessen.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        normpackungsgroesse: Normpackungsgroessen | None = results.one_or_none()
        if normpackungsgroesse is None and raise_exception_if_none:
            raise raise_exception_if_none
        return normpackungsgroesse

    async def create(
        self,
        normpackungsgroesse_create: Normpackungsgroessen,
        raise_exception_if_exists: Exception = None,
    ) -> Normpackungsgroessen:
        log.debug(f"Create normpackungsgroessen: {normpackungsgroesse_create}")
        existing_normpackungsgroesse = None
        if raise_exception_if_exists:
            existing_normpackungsgroesse = self.get(
                zuzahlstufe=normpackungsgroesse_create.zuzahlstufe,
                ai_version_id=normpackungsgroesse_create.ai_version_id,
            )

        if existing_normpackungsgroesse and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_normpackungsgroesse:
            return existing_normpackungsgroesse
        self.session.add(normpackungsgroesse_create)
        await self.session.commit()
        await self.session.refresh(normpackungsgroesse_create)
        return normpackungsgroesse_create

    async def create_bulk(
        self,
        objects: List[Normpackungsgroessen],
    ) -> Normpackungsgroessen:
        log.debug(f"Create bulk of normpackungsgroessen")
        for obj in objects:
            if not isinstance(obj, Normpackungsgroessen):
                raise ValueError(
                    f"List item is not a Normpackungsgroessen instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        normpackungsgroessen_update: Normpackungsgroessen,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Normpackungsgroessen:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        normpackungsgroessen_normpackungsgroessen: str,
        ai_version_id: str | UUID = None,
    ) -> Normpackungsgroessen:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_normpackungsgroessen_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[NormpackungsgroessenCRUD, None]:
    yield NormpackungsgroessenCRUD(session=session)


get_normpackungsgroessen_crud_context = contextlib.asynccontextmanager(
    get_normpackungsgroessen_crud
)
