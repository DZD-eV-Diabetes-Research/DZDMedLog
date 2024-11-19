from typing import Dict, List, AsyncIterator, Literal, Optional
import traceback
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
from medlogserver.model.drug_data.drug_attr import DrugVal, DrugValRef
from medlogserver.model.drug_data.drug import DrugData
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

    async def get_all_attr_field_definitions(
        self,
    ) -> Dict[
        Literal["attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref"],
        List[DrugAttrFieldDefinition],
    ]:
        return {
            "attrs": await self.get_attr_field_definitions(),
            "attrs_ref": await self.get_attr_ref_field_definitions(),
            "attrs_multi": await self.get_attr_multi_field_definitions(),
            "attrs_multi_ref": await self.get_attr_multi_ref_field_definitions(),
        }

    async def get_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_multi_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_multi_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_code_definitions(self) -> List[DrugCodeSystem]:
        raise NotImplementedError()

    async def get_drug_items(self) -> AsyncIterator[DrugData]:
        raise NotImplementedError()

    async def run_import(self, source_dir: Path, version: str):
        raise NotImplementedError()

    async def _run_import(self, source_dir: Path, version: str):
        self.version = version
        self.source_dir = source_dir
        already_imported_datasets = await self.get_already_imported_datasets()

        drug_dataset = await self._ensure_drug_dataset_version(
            self.source_dir, self.version
        )
        drug_custom_dataset = await self._ensure_custom_drug_dataset_version()

        if drug_dataset.dataset_version in [
            imported_ds.dataset_version for imported_ds in already_imported_datasets
        ]:
            loaded_dataset = next(
                imported_ds
                for imported_ds in already_imported_datasets
                if imported_ds.dataset_version == drug_dataset.dataset_version
            )
            if loaded_dataset.import_status != "failed":
                log.info(
                    f"[DRUG DATA IMPORT] Dataset '{drug_dataset.dataset_source_name}' with version '{drug_dataset.dataset_version}' already imported. Skip drug data import."
                )
                return
        log.info(f"[DRUG DATA IMPORT] Start import of '{source_dir}'...")
        await self._set_dataset_version_status("running")
        try:
            await self.run_import(source_dir, version)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(
                f"[DRUG DATA IMPORT] Import '{drug_dataset.dataset_source_name}' with version '{drug_dataset.dataset_version}' failed. Error:"
            )
            log.error(tb)
            self._set_dataset_version_status(status="failed", error=tb)
            log.info("")
            raise e
            return

        await self._finish_import(source_dir=source_dir, version=version)

    async def _finish_import(self, source_dir: Path, version: str):
        await self._set_dataset_version_status("done")

    async def get_already_imported_datasets(self) -> List[DrugDataSetVersion]:
        async with get_async_session_context() as session:
            query = (
                select(DrugDataSetVersion)
                .where(
                    and_(
                        DrugDataSetVersion.dataset_source_name == self.dataset_name,
                        DrugDataSetVersion.is_custom_drugs_collection == False,
                    )
                )
                .order_by(DrugDataSetVersion.dataset_version)
            )
            result = await session.exec(query)
            return result.all()

    async def _ensure_drug_dataset_version(
        self, source_dir: Path = None, version: str = None
    ) -> DrugDataSetVersion:
        """Return a DrugDataSetVersion for this drug dataset. Will be created if not allready existent

        Args:
            source_dir (Path): _description_
            version (str): _description_

        Returns:
            DrugDataSetVersion: _description_
        """
        if source_dir is None:
            source_dir = self.source_dir
        if version is None:
            version = self.version

        async with get_async_session_context() as session:
            drug_dataset_query = select(DrugDataSetVersion).where(
                and_(
                    DrugDataSetVersion.dataset_source_name == self.dataset_name,
                    DrugDataSetVersion.is_custom_drugs_collection == False,
                    DrugDataSetVersion.dataset_version == version,
                )
            )
            drug_dataset_res = await session.exec(drug_dataset_query)
            drug_dataset = drug_dataset_res.one_or_none()
            if drug_dataset is None:
                log.info("[DRUG DATA IMPORT] Create dataset version entry...")
                drug_dataset = await self.generate_drug_data_set_definition()
                drug_dataset.import_start_datetime_utc = datetime.datetime.now(
                    tz=datetime.timezone.utc
                )
                drug_dataset.import_file_path = str(Path(source_dir).resolve())
                async with get_async_session_context() as session:
                    session.add(drug_dataset)
                    await session.commit()
        return drug_dataset

    async def _ensure_custom_drug_dataset_version(
        self,
    ) -> DrugDataSetVersion:
        """Return a DrugDataSetVersion for custom drug in this drug dataset. Will be created if not allready existent

        Returns:
            DrugDataSetVersion: _description_
        """
        async with get_async_session_context() as session:
            custom_drug_dataset_query = select(DrugDataSetVersion).where(
                and_(
                    DrugDataSetVersion.dataset_source_name == self.dataset_name,
                    DrugDataSetVersion.is_custom_drugs_collection == True,
                )
            )
            custom_drug_dataset_res = await session.exec(custom_drug_dataset_query)
            custom_drug_dataset = custom_drug_dataset_res.one_or_none()
            if custom_drug_dataset is None:
                custom_drug_dataset = await self.generate_custom_drug_set_definition()
                custom_drug_dataset.import_start_datetime_utc = datetime.datetime.now(
                    tz=datetime.timezone.utc
                )
                custom_drug_dataset.import_status = "done"
                async with get_async_session_context() as session:
                    session.add(custom_drug_dataset)
                    await session.commit()
        return custom_drug_dataset

    async def _set_dataset_version_status(
        self, status: Literal["queued", "running", "failed" "done"], error: str = None
    ) -> DrugDataSetVersion:
        dataset_version: DrugDataSetVersion = await self._ensure_drug_dataset_version()
        if dataset_version.import_status == status and error is None:
            return dataset_version
        dataset_version.import_status = status
        dataset_version.import_error = error
        async with get_async_session_context() as session:
            session.add(dataset_version)
            await session.commit()
        return dataset_version

    async def generate_drug_dataset_schema(
        self, source_dir: Path, version: str
    ) -> List[DrugAttrFieldDefinition | DrugCodeSystem]:
        all_objs = []
        attr_defs = await self.get_attr_field_definitions()
        all_objs.extend(attr_defs)
        lov_field_objects = await self.get_attr_ref_field_definitions()
        for lov_field_obj in lov_field_objects:
            all_objs.append(lov_field_obj)

        all_objs.extend(await self.get_code_definitions())
        return all_objs
