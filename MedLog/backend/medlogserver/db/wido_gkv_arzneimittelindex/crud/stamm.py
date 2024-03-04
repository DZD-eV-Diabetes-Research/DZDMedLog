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
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm import Stamm, StammRead
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StammCRUD(DrugCRUDBase[Stamm, StammRead, Stamm, Stamm]):
    _table_ = Stamm

    async def get_multiple(
        self,
        pzns: List[str],
        current_version_only: bool = True,
        pagination: QueryParamsInterface = None,
        keep_pzn_order: bool = True,
    ) -> Sequence[StammRead]:
        query = select(Stamm).where(col(Stamm.pzn).in_(pzns))
        if current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Stamm.ai_version_id == current_ai_version.id)
        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_pzn_order:
            db_order: List[StammRead] = results.all()
            new_order: List[StammRead] = []
            for pzn in pzns:
                db_order_item_index = next(
                    (i for i, obj in enumerate(db_order) if obj.pzn == pzn)
                )
                item = db_order.pop(db_order_item_index)
                new_order.append(item)
            return new_order
        return results.all()
