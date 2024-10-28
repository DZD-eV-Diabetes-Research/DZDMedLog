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
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.wido_gkv_arzneimittelindex.stamm import (
    StammUserCustom,
    StammUserCustomCreateAPI,
    StammUserCustomRead,
)
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex._base import create_drug_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StammUserCustomCRUD(
    create_drug_crud_base(
        table_model=StammUserCustom,
        read_model=StammUserCustomRead,
        create_model=StammUserCustom,
        update_model=StammUserCustom,
    )
):
    async def get_multiple(
        self,
        ids: List[uuid.UUID],
        pagination: QueryParamsInterface = None,
        keep_pzn_order: bool = True,
    ) -> Sequence[StammUserCustomRead]:
        query = select(StammUserCustom).where(col(StammUserCustom.id).in_(ids))
        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_pzn_order:
            db_order: List[StammUserCustomRead] = results.all()
            new_order: List[StammUserCustomRead] = []
            for pzn in ids:
                db_order_item_index = next(
                    (i for i, obj in enumerate(db_order) if obj.pzn == pzn)
                )
                item = db_order.pop(db_order_item_index)
                new_order.append(item)
            return new_order
        return results.all()

    async def list(
        self, filter_user_id: uuid.UUID, pagination: QueryParamsInterface = None
    ) -> StammUserCustom:
        query = select(StammUserCustom)
        if filter_user_id:
            query = query.where(StammUserCustom.created_by_user == filter_user_id)
        query_result = await self.session.exec(statement=query)
        return query_result.all()
