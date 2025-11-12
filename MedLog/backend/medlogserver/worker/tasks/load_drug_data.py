from typing import List, Dict, Type, Callable, Optional, Tuple
import importlib

from pathlib import Path, PurePath
from dataclasses import dataclass
import yaml
import traceback

# internal imports
from medlogserver.worker.task import TaskBase
import pydantic
import gc

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.utils import to_path, get_default_file_data
from medlogserver.db._session import get_async_session_context
from medlogserver.model import MedLogBaseModel
from medlogserver.db._base_crud import CRUDBase
from medlogserver.db import (
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
    EventCRUD,
    InterviewCRUD,
    IntakeCRUD,
    WorkerJobCRUD,
)
from medlogserver.db.drug_data.drug_dataset_version import (
    DrugDataSetVersionCRUD,
    DrugDataSetVersion,
)
from medlogserver.api.paginator import QueryParamsInterface, create_query_params_class

log = get_logger()
config = Config()
CRUD_classes: List[CRUDBase] = [
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
    EventCRUD,
    InterviewCRUD,
    IntakeCRUD,
    WorkerJobCRUD,
]


class DrugDataLoader:
    def __init__(self):
        from medlogserver.db.drug_data.importers import DRUG_IMPORTERS

        self.importer_class: Type[DrugDataSetImporterBase] = DRUG_IMPORTERS[
            config.DRUG_IMPORTER_PLUGIN
        ]
        self.importer = self.importer_class()

    async def _create_inital_drugdataset_entry_if_needed(self):
        if not config.DRUG_TABLE_PROVISIONING_SOURCE_DIR:
            return

        async with get_async_session_context() as session:
            async with DrugDataSetVersionCRUD.crud_context(
                session
            ) as drugdataset_version_crud:
                drugdataset_version_crud: DrugDataSetVersionCRUD = (
                    drugdataset_version_crud
                )
                drugdataset_count = await drugdataset_version_crud.count()
                log.debug(
                    f"Check if inital dataset needs to be created. count: {drugdataset_count}"
                )
                if drugdataset_count == 0:
                    self.importer.source_dir = config.DRUG_TABLE_PROVISIONING_SOURCE_DIR
                    self.importer.version = (
                        await self.importer.get_drug_dataset_version()
                    )
                    initial_dataset = (
                        await self.importer.generate_drug_data_set_definition()
                    )
                    initial_dataset.import_path = self.importer.source_dir
                    await drugdataset_version_crud.create(initial_dataset)

    async def _get_next_queued_drug_data_set(self) -> DrugDataSetVersion | None:
        async with get_async_session_context() as session:
            async with DrugDataSetVersionCRUD.crud_context(
                session
            ) as drugdataset_version_crud:
                drugdataset_version_crud: DrugDataSetVersionCRUD = (
                    drugdataset_version_crud
                )
                DrugDataSetVersionQueryParams: Type[QueryParamsInterface] = (
                    create_query_params_class(DrugDataSetVersion)
                )

                queued_drug_data_sets = await drugdataset_version_crud.list(
                    filter_import_status="queued",
                    filter_is_custom_drug_collection=False,
                    pagination=DrugDataSetVersionQueryParams(
                        order_by="dataset_version", order_desc=True
                    ),
                )
                log.debug(
                    f"_get_next_queued_drug_data_set result. {queued_drug_data_sets}"
                )
                first_queued_drug_data_set = None
                if queued_drug_data_sets:
                    first_queued_drug_data_set = queued_drug_data_sets[0]
        return first_queued_drug_data_set

    async def _rebuild_drugsearch_index(self):
        from medlogserver.db.drug_data.drug_search._base import (
            MedLogDrugSearchEngineBase,
        )
        from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
            GenericSQLDrugSearchEngine,
        )
        from medlogserver.db.drug_data.drug_search import SEARCH_ENGINES

        log.info("Build drug search index if needed...")
        search_engine_class: Type[MedLogDrugSearchEngineBase] = SEARCH_ENGINES[
            config.DRUG_SEARCHENGINE_CLASS
        ]
        search_engine: GenericSQLDrugSearchEngine = search_engine_class()

        await search_engine.build_index()

    async def load_new_drug_data_if_available(self):
        await self._create_inital_drugdataset_entry_if_needed()
        drug_dataset = await self._get_next_queued_drug_data_set()
        if drug_dataset:
            log.debug(f"Import drug dataset: {drug_dataset}")
            await self.importer._run_import(source_dir=drug_dataset.import_path)
            await self._rebuild_drugsearch_index()
            gc.collect()
        else:
            log.info("...no new drug data available.")


class TaskDrugDataLoading(TaskBase):
    async def work(self, source_dir: str = None):
        log.info("Load new drug data if available...")
        drug_data_loader = DrugDataLoader()

        await drug_data_loader.load_new_drug_data_if_available()
