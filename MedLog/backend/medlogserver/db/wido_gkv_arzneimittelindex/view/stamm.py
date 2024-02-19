from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel
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
from medlogserver.db.wido_gkv_arzneimittelindex.view._base import DrugViewBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()


class StammJoinedView(DrugViewBase):
    async def search(self, current_version_only: bool = True) -> Sequence[Stamm]:
        query = select(Stamm.darrform.darrform)
        query = select(func.count(Stamm.pzn))
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)

        results = await self.session.exec(statement=query)
        print("results", results)
        return results.first()


async def get_stamm_view(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[StammView, None]:
    yield StammView(session=session)


get_stamm_view_context = contextlib.asynccontextmanager(get_stamm_view)
