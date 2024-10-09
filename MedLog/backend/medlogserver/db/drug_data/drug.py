from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func, col, desc
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import Drug
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS

log = get_logger()
config = Config()


class DrugCRUD(
    create_crud_base(
        table_model=Drug,
        read_model=Drug,
        create_model=Drug,
        update_model=Drug,
    )
):
    async def append_current_dataset_version_where_clause(
        self, query: sqlEpression.Select
    ):
        drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        drug_importer = drug_importer_class()

        sub_query = (
            select(DrugDataSetVersion)
            .where(DrugDataSetVersion.dataset_name == drug_importer.dataset_name)
            .order_by(desc(DrugDataSetVersion.current_active))
            .order_by(desc(DrugDataSetVersion.dataset_version))
            .limit(1)
            .scalar_subquery()
        )
        query.where(Drug.source_dataset_id == sub_query)
        return query

    async def count(
        self,
    ) -> int:
        query = select(func.count()).select_from(Drug)
        query = await self.append_current_dataset_version_where_clause(query)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        filter_study_id: UUID = None,
        hide_completed: bool = False,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[Drug]:
        if isinstance(filter_study_id, str):
            filter_study_id: UUID = UUID(filter_study_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(Drug)
        query = await self.append_current_dataset_version_where_clause(query)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get_multiple(
        self,
        ids: List[str],
        pagination: QueryParamsInterface = None,
        keep_result_in_ids_order: bool = True,
    ) -> Sequence[Drug]:
        query = select(Drug).where(col(Drug.id).in_(ids))
        query = await self.append_current_dataset_version_where_clause(query)

        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_result_in_ids_order:
            # todo: maybe we can solve the drug order in sql?
            db_order: List[Drug] = results.all()
            new_order: List[Drug] = []
            for drug_id in ids:
                db_order_item_index = next(
                    (i for i, obj in enumerate(db_order) if obj.id == drug_id)
                )
                item = db_order.pop(db_order_item_index)
                new_order.append(item)
            return new_order
        return results.all()
