from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, col, func

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable
from medlogserver.model.wido_gkv_arzneimittelindex.hersteller import (
    Hersteller,
)
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex._base import create_drug_crud_base

log = get_logger()
config = Config()


class HerstellerCRUD(
    create_drug_crud_base(
        table_model=Hersteller,
        read_model=Hersteller,
        create_model=Hersteller,
        update_model=Hersteller,
    )
):

    async def list(
        self,
        current_version_only: bool = True,
        search_term: str = None,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[Hersteller]:
        query = select(Hersteller)
        if not self._is_ai_versionless_table_ and current_version_only:
            current_ai_version: AiDataVersion = await self._get_current_ai_version()
            query = query.where(Hersteller.ai_dataversion_id == current_ai_version.id)
        if search_term:
            query = query.where(
                col(func.lower(Hersteller.bedeutung)).contains(search_term.lower())
                or col(func.lower(Hersteller.herstellercode)).contains(
                    search_term.lower()
                )
            )
        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        res = results.all()
        return res
