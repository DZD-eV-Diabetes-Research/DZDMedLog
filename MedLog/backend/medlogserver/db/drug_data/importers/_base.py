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
from medlogserver.utils import PathContentHasher
from medlogserver.log import get_logger
import time

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

    async def get_drug_dataset_version(self) -> str:
        # generic way of creating a version string.
        # if there is more effiecient way for a certain dataset like a date in the directory, overwrite this function.
        # if this method is overwritten, the method "is_dataset_imported()" must be adapted as well.
        source_dir_hash = PathContentHasher.md5_dir(self.source_dir)
        epoch_time = int(time.time())
        version_string = f"{epoch_time}_{source_dir_hash}"
        return version_string

    async def was_dataset_version_imported(self) -> DrugDataSetVersion | None:
        # this function is apt to work with method get_drug_dataset_version()
        # if get_drug_dataset_version() is overwriten this method needs to be adpated/overwriten as well.
        epoch_time, source_dir_hash = self.version.split("_")
        imported_datasets = await self.get_already_imported_datasets()
        for imported_dataset in imported_datasets:
            imported_epoch_time, imported_source_dir_hash = (
                imported_dataset.dataset_version.split("_")
            )
            if source_dir_hash == imported_source_dir_hash:
                print("source_dir_hash", source_dir_hash)
                print("imported_source_dir_hash", imported_source_dir_hash)
                return imported_dataset
        return None

    async def get_all_attr_field_definitions(
        self,
    ) -> Dict[
        Literal["attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref"],
        List[DrugAttrFieldDefinition],
    ]:
        return {
            "codes": await self.get_code_definitions(),
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

    async def run_import(self, source_dir: Path):
        raise NotImplementedError()

    async def _run_import(self, source_dir: Path):

        self.source_dir = source_dir
        self.version = await self.get_drug_dataset_version()
        dataset_with_same_version_imported = await self.was_dataset_version_imported()
        if dataset_with_same_version_imported is not None:
            if dataset_with_same_version_imported.import_status == "failed":
                log.warning(
                    f"[DRUG DATA IMPORT] Dataset '{self.dataset_name}' with version '{self.version}' failed last time. Error:\n {dataset_with_same_version_imported.import_error}"
                )
                time.sleep(2)
            else:
                log.info(
                    f"[DRUG DATA IMPORT] Dataset '{self.dataset_name}' with version '{self.version}' already imported. Skip drug data import."
                )
            return
        drug_dataset = await self._ensure_drug_dataset_version()
        drug_custom_dataset = await self._ensure_custom_drug_dataset_version()

        log.info(f"[DRUG DATA IMPORT] Start import of '{self.source_dir}'...")
        await self._set_dataset_version_status("running")
        try:
            await self.run_import()
        except Exception as e:
            tb = traceback.format_exc()
            log.error(
                f"[DRUG DATA IMPORT] Import '{drug_dataset.dataset_source_name}' with version '{drug_dataset.dataset_version}' failed. Error:"
            )
            log.error(tb)
            await self._set_dataset_version_status(status="failed", error=tb)
            log.info("")
            raise e
            return

        await self._finish_import()

    async def _finish_import(self):
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

    async def _ensure_drug_dataset_version(self) -> DrugDataSetVersion:
        """Return a DrugDataSetVersion for this drug dataset. Will be created if not allready existent

        Args:
            source_dir (Path): _description_
            version (str): _description_

        Returns:
            DrugDataSetVersion: _description_
        """

        source_dir = self.source_dir
        if source_dir is None:
            raise ValueError(
                f"DrugDataSet {self.dataset_name} has no source_dir yet. Was drug data impoerter method `_ensure_drug_dataset_version` called without providing a source_dir."
            )
        version = self.version
        if version is None:
            raise ValueError(
                f"DrugDataSet {self.dataset_name} has not version yet. Was drug data impoerter method `_ensure_drug_dataset_version` called before producing a version string."
            )

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
