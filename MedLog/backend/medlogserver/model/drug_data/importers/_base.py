from typing import Dict, List, AsyncIterator
from pathlib import Path
import datetime
from sqlmodel import select, and_
from medlogserver.db._session import get_async_session_context
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data._base import DrugModelTableBase
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug import Drug
from medlogserver.log import get_logger

log = get_logger()


class DrugDataSetImporterBase:
    def __init__(self):
        self.dataset_name = "Base Example"
        self.dataset_link = "Base Example"
        self.api_name = "baseexample"
        self.source_dir: Path = None
        self.version: str = None

    async def generate_drug_data_set_definition(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version=self.version,
            dataset_source_name=self.dataset_name,
            dataset_link=self.dataset_link,
        )

    async def generate_custom_drug_set_definition(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version="Custom",
            is_custom_drugs_collection=True,
            dataset_source_name=self.dataset_name,
        )

    async def get_ref_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_code_definitions(self) -> List[DrugCodeSystem]:
        raise NotImplementedError()

    async def get_drug_items(self) -> AsyncIterator[Drug]:
        raise NotImplementedError()

    async def _run_import(self, source_dir: Path, version: str):
        self.version = version
        self.source_dir = source_dir
        self._ensure_drug_dataset_version()

        drug_dataset = await self.generate_drug_data_set_definition()
        already_imported_datasets = await self.get_already_imported_datasets()

        if drug_dataset.dataset_version in [
            imported_ds.dataset_version for imported_ds in already_imported_datasets
        ]:
            log.info(
                f"[DRUG DATA IMPORT] Dataset '{drug_dataset.dataset_source_name}' with version '{drug_dataset.dataset_version}' already imported. Skip drug data import."
            )
            return
        await self.run_import(source_dir, version)

    async def run_import(self, source_dir: Path, version: str):
        raise NotImplementedError()

    async def get_already_imported_datasets(self) -> List[DrugDataSetVersion]:
        async with get_async_session_context() as session:
            query = select(DrugDataSetVersion).where(
                DrugDataSetVersion.dataset_source_name == self.dataset_name
            )
            result = await session.exec(query)
            return result.all()

    async def get_drug_dataset_schema(
        self, source_dir: Path, version: str
    ) -> List[DrugDataSetVersion | DrugAttrFieldDefinition | DrugCodeSystem]:
        self.source_dir = source_dir
        self.version = version
        log.info("[DRUG DATA IMPORT] Parse metadata...")
        drug_dataset = await self.generate_drug_data_set_definition()
        custom_drug_dataset = await self.generate_custom_drug_set_definition()

        drug_dataset.import_datetime_utc = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        custom_drug_dataset.import_datetime_utc = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        all_objs = [drug_dataset, custom_drug_dataset]
        attr_defs = await self.get_attr_field_definitions()
        all_objs.extend(attr_defs)
        lov_field_objects = await self.get_ref_attr_field_definitions()
        for lov_field_obj in lov_field_objects:
            all_objs.append(lov_field_obj)

        all_objs.extend(await self.get_code_definitions())
        return all_objs

    async def _ensure_drug_dataset_version(
        self, source_dir: Path = None, version: str = None
    ):
        if source_dir is None:
            source_dir = self.source_dir
        if version is None:
            version = self.version
            # yah
        with 
        select(DrugDataSetVersion).where(
            and_(
                DrugDataSetVersion.dataset_source_name == self.dataset_name,
                DrugDataSetVersion.dataset_version == version,
            )
        )

    async def _ensure_custom_drug_dataset_version(self):
        pass

    async def _finish_import(self, source_dir: Path, version: str):
        pass

    async def _set_drug_dataset_status(self, status: str, error: str):
        pass
