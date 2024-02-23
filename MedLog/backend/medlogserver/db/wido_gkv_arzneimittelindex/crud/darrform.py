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
from medlogserver.db.wido_gkv_arzneimittelindex.model.darrform import (
    Darreichungsform,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase

log = get_logger()
config = Config()


class DarreichungsformCRUD(DrugCRUDBase):
    _table_ = Darreichungsform

    async def get(
        self,
        darrform: str,
        ai_version_id: uuid.UUID | str = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Darreichungsform]:
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

        query = select(Darreichungsform).where(
            Darreichungsform.darrform == darrform
            and Darreichungsform.ai_version_id == ai_version_id
        )

        results = await self.session.exec(statement=query)
        darrform: Darreichungsform | None = results.one_or_none()
        if darrform is None and raise_exception_if_none:
            raise raise_exception_if_none
        return darrform

    async def create(
        self,
        darrform_create: Darreichungsform,
        raise_exception_if_exists: Exception = None,
    ) -> Darreichungsform:
        log.debug(f"Create darrform: {darrform_create}")
        existing_darrform = None
        if raise_exception_if_exists:
            existing_darrform = self.get(
                darrform=darrform_create.darrform,
                ai_version_id=darrform_create.ai_version_id,
            )

        if existing_darrform and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_darrform:
            return existing_darrform
        self.session.add(darrform_create)
        await self.session.commit()
        await self.session.refresh(darrform_create)
        return darrform_create

    async def create_bulk(
        self,
        objects: List[Darreichungsform],
    ) -> Darreichungsform:
        log.debug(f"Create bulk of darrform")
        for obj in objects:
            if not isinstance(obj, Darreichungsform):
                raise ValueError(
                    f"List item is not a Darreichungsform instance:\n {objects}"
                )
        self.session.add_all(objects)
        await self.session.commit()

    async def update(
        self,
        darrform_update: Darreichungsform,
        ai_version_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> Darreichungsform:
        # atm we dont need (or even dont want) an update endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        raise NotImplementedError()
        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id

    async def delete(
        self,
        darrform_darrform: str,
        ai_version_id: str | UUID = None,
    ) -> Darreichungsform:
        # atm we dont need (or even dont want) an delete endpoint.
        # after import of the arzneimittelindex data, the data should be kind of "read only"
        # deletions will only happen when a whole Arbeimittelindex "version"-set is deleted. that will happen by casade deletion
        raise NotImplementedError()

        if ai_version_id is None:
            current_ai_version = await self._get_current_ai_version()
            ai_version_id = current_ai_version.id


async def get_darrform_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[DarreichungsformCRUD, None]:
    yield DarreichungsformCRUD(session=session)


get_darrform_crud_context = contextlib.asynccontextmanager(get_darrform_crud)
