from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func, col
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
    DrugAttrFieldLovItemCREATE,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS

log = get_logger()
config = Config()


class DrugAttrFieldLovItemCRUD(
    create_crud_base(
        table_model=DrugAttrFieldLovItem,
        read_model=DrugAttrFieldLovItem,
        create_model=DrugAttrFieldLovItemCREATE,
        update_model=DrugAttrFieldLovItem,
    )
):
    async def count(
        self,
        field_name: str,
    ) -> int:
        query = (
            select(func.count())
            .select_from(DrugAttrFieldLovItem)
            .where(DrugAttrFieldLovItem.field_name == field_name)
        )
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        field_name: str,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[DrugAttrFieldLovItem]:
        query = select(DrugAttrFieldLovItem).where(
            DrugAttrFieldLovItem.field_name == field_name
        )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()
