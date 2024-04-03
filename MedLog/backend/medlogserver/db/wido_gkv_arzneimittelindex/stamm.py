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
from medlogserver.model._base_model import MedLogBaseModel, BaseTable
from medlogserver.model.wido_gkv_arzneimittelindex.stamm import Stamm, StammRead
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex._base import create_drug_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StammCRUD(
    create_drug_crud_base(
        table_model=Stamm,
        read_model=StammRead,
        create_model=Stamm,
        update_model=Stamm,
    )
):

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
