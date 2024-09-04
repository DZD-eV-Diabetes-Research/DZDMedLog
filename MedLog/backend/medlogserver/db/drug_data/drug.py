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
    async def attach_latest_dataset_version_where_cause(
        self, query: sqlEpression.Select
    ):
        drug_importer = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        dataset_class = await drug_importer.get_drug_data_set()
        select(DrugDataSetVersion.id).where(
            func.max(DrugDataSetVersion.dataset_version)
            and DrugDataSetVersion.dataset_name == dataset_class.dataset_name
        ).limit(1)
        query.where(Drug.source_dataset_id == select)

    async def count(
        self,
    ) -> int:
        query = select(func.count()).select_from(Drug)
        query = await self.attach_latest_dataset_version_where_cause(query)
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
        query = await self.attach_latest_dataset_version_where_cause(query)
        results = await self.session.exec(statement=query)
        return results.all()
