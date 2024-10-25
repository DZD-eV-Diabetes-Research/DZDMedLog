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
import datetime

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import Drug
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase

log = get_logger()
config = Config()


class DrugDataSetVersionCRUD(
    create_crud_base(
        table_model=DrugDataSetVersion,
        read_model=DrugDataSetVersion,
        create_model=DrugDataSetVersion,
        update_model=DrugDataSetVersion,
    )
):

    def _get_current_dataset_name(self) -> str:
        drug_importer_class: DrugDataSetImporterBase = DRUG_IMPORTERS[
            config.DRUG_IMPORTER_PLUGIN
        ]()
        return drug_importer_class.dataset_name

    async def list(self) -> List[DrugDataSetVersion]:
        query = (
            select(DrugDataSetVersion)
            .where(
                DrugDataSetVersion.dataset_source_name
                == self._get_current_dataset_name()
            )
            .order_by(DrugDataSetVersion.dataset_version)
        )

        results = await self.session.exec(statement=query)
        return results.all()

    async def count(
        self,
    ) -> int:
        query = select(DrugDataSetVersion).where(
            DrugDataSetVersion.dataset_source_name == self._get_current_dataset_name()
        )
        results = await self.session.exec(statement=query)
        return results.first()

    async def get_current(self) -> DrugDataSetVersion | None:
        query = (
            select(DrugDataSetVersion)
            .where(
                DrugDataSetVersion.dataset_source_name
                == self._get_current_dataset_name()
                and DrugDataSetVersion.is_custom_drugs_collection == False
            )
            .order_by(desc(DrugDataSetVersion.current_active))
            .order_by(desc(DrugDataSetVersion.dataset_version))
            .limit(1)
        )
        results = await self.session.exec(statement=query)
        return results.one_or_none()

    async def get_custom(
        self,
    ) -> DrugDataSetVersion | None:
        query = (
            select(DrugDataSetVersion)
            .where(
                DrugDataSetVersion.dataset_source_name
                == self._get_current_dataset_name()
                and DrugDataSetVersion.is_custom_drugs_collection == True
            )
            .limit(1)
        )
        results = await self.session.exec(statement=query)
        return results.one_or_none()

        # old code can be removed
        current_drug_dataset = await self.get_current()
        if current_drug_dataset is None:
            return None
        custom_drug_dataset_query = select(DrugDataSetVersion).where(
            DrugDataSetVersion.is_custom_drugs_collection == True
            and DrugDataSetVersion.dataset_source_name
            == current_drug_dataset.dataset_source_name
        )
        result = await self.session.exec(custom_drug_dataset_query)
        custom_drug_dataset = result.one_or_none()
        if custom_drug_dataset:
            return custom_drug_dataset
        custom_drug_dataset = DrugDataSetVersion(
            is_custom_drugs_collection=True,
            dataset_version="CUSTOM",
            dataset_source_name=current_drug_dataset.dataset_source_name,
            import_status="Done",
            import_datetime_utc=datetime.datetime.now(tz=datetime.UTC),
        )
        self.session.add(custom_drug_dataset)
        await self.session.commit()
        await self.session.refresh(custom_drug_dataset)
        return custom_drug_dataset
