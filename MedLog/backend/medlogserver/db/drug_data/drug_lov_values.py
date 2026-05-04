from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import (
    Field,
    select,
    delete,
    Column,
    JSON,
    SQLModel,
    func,
    col,
    or_,
    and_,
    desc,
)
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import DrugData
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
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS

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
    async def append_current_dataset_version_where_clause(
        self, query: sqlEpression.Select
    ):
        drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        drug_importer = drug_importer_class()
        # todo: this probably can be optimized...

        sub_query = (
            select(DrugDataSetVersion.id)
            .where(DrugDataSetVersion.dataset_source_name == drug_importer.dataset_name)
            .where(DrugDataSetVersion.is_custom_drugs_collection.is_(False))
            .order_by(desc(DrugDataSetVersion.current_active))
            .order_by(desc(DrugDataSetVersion.dataset_version))
            .limit(1)
            .scalar_subquery()
        )
        query = query.where(
            DrugAttrFieldLovItem.drug_dataset_version_fk == sub_query,
        )
        return query

    async def count(
        self,
        field_name: str,
        search_term: str = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(DrugAttrFieldLovItem)
            .where(DrugAttrFieldLovItem.field_name == field_name)
        )
        if search_term:
            query = query.where(
                or_(
                    col(DrugAttrFieldLovItem.value).icontains(search_term),
                    col(DrugAttrFieldLovItem.display).icontains(search_term),
                )
            )
        query = await self.append_current_dataset_version_where_clause(query)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        field_name: str,
        search_term: str = None,
        pagination: Optional[QueryParamsInterface] = None,
    ) -> List[DrugAttrFieldLovItem]:
        query = select(DrugAttrFieldLovItem).where(
            DrugAttrFieldLovItem.field_name == field_name
        )
        if search_term:
            query = query.where(
                or_(
                    col(DrugAttrFieldLovItem.value).icontains(search_term),
                    col(DrugAttrFieldLovItem.display).icontains(search_term),
                )
            )
        query = await self.append_current_dataset_version_where_clause(query)
        log.debug(f"query list {query}")
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        field_name: str,
        value: str,
        raise_exception_if_none: Exception = None,
    ) -> DrugAttrFieldLovItem | None:
        query = select(DrugAttrFieldLovItem).where(
            and_(
                DrugAttrFieldLovItem.field_name == field_name,
                DrugAttrFieldLovItem.value == value,
            )
        )
        query = await self.append_current_dataset_version_where_clause(query)
        result = await self.session.exec(statement=query)
        obj = result.one_or_none()
        if obj is None and raise_exception_if_none:
            raise raise_exception_if_none
        return obj
