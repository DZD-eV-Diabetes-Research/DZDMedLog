from typing import List, Optional, Sequence, Type
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import func, select
from uuid import UUID
from medlogserver.db.wido_gkv_arzneimittelindex.model._base import (
    DrugModelTableBase,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud.ai_data_version import (
    AiDataVersionCRUD,
    get_ai_data_version_crud,
    get_ai_data_version_crud_context,
)


from medlogserver.api.paginator import PageParams


class DrugCRUDBase:
    _table_: Type[DrugModelTableBase] = None
    _ai_versionless_table_: bool = False

    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def count(self, current_version_only: bool = True) -> int:
        table: DrugModelTableBase = getattr(self, "_table_", None)
        if table is None:
            raise NotImplementedError
        query = select(func.count()).select_from(table)
        if not self._ai_versionless_table_ and current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(table.ai_version_id == current_ai_version.id)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self, current_version_only: bool = True, pagination: PageParams = None
    ) -> Sequence[_table_]:
        query = select(self._table_)
        if not self._ai_versionless_table_ and current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(self._table_.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def _get_current_ai_version(
        self,
    ) -> AiDataVersion:
        if self._ai_versionless_table_:
            raise ValueError("Does not make any sense. Remove this tim")
        if self._current_ai_version is None:
            async with get_ai_data_version_crud_context(
                self.session
            ) as ai_version_crud:
                self._current_ai_version = await ai_version_crud.get_current()

        return self._current_ai_version

    def create_bulk(self, objects: List[DrugModelTableBase]):
        # this is just an abstract/interface method.
        # look into the specific class file at MedLog/backend/medlogserver/db/wido_gkv_arzneimittelindex/crud/* for specific implementations
        raise NotImplementedError()
