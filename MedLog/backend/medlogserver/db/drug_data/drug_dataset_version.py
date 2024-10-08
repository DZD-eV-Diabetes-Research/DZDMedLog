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

    def _get_active_dataset_name(self) -> str:
        drug_importer_class: DrugDataSetImporterBase = DRUG_IMPORTERS[
            config.DRUG_IMPORTER_PLUGIN
        ]()
        return drug_importer_class.dataset_name

    async def list(self) -> List[DrugDataSetVersion]:
        query = (
            select(DrugDataSetVersion)
            .where(DrugDataSetVersion.dataset_name == self._get_active_dataset_name())
            .order_by(DrugDataSetVersion.dataset_version)
        )

        results = await self.session.exec(statement=query)
        return results.all()

    async def count(
        self,
    ) -> int:
        query = select(DrugDataSetVersion).where(
            DrugDataSetVersion.dataset_name == self._get_active_dataset_name()
        )
        results = await self.session.exec(statement=query)
        return results.first()

    async def get_current(self) -> DrugDataSetVersion | None:
        query = (
            select(DrugDataSetVersion)
            .where(DrugDataSetVersion.dataset_name == self._get_active_dataset_name())
            .order_by(desc(DrugDataSetVersion.current_active))
            .order_by(desc(DrugDataSetVersion.dataset_version))
            .limit(1)
        )
        results = await self.session.exec(statement=query)
        return results.one_or_none()
