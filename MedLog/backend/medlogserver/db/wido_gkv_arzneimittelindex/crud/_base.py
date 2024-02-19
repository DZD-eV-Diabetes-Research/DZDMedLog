from typing import List
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

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


class DrugCRUDBase:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._current_ai_version: AiDataVersion = None

    async def _get_current_ai_version(
        self,
    ) -> AiDataVersion:
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
