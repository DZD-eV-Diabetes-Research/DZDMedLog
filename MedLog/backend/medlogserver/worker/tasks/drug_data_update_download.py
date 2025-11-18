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


class DrugDataUpdateDownloader:
    def __init__(self):
        from medlogserver.db.drug_data.importers import DRUG_IMPORTERS

        self.importer_class: Type[DrugDataSetImporterBase] = DRUG_IMPORTERS[
            config.DRUG_IMPORTER_PLUGIN
        ]

    async def download_new_drug_data_update_if_available(self):
        log.info("[DRUG DATA DOWNLOADER]: Check for new updates of drug data...")
        if self.importer_class.check_for_remote_dataset_update_available() is None:
            log.info(
                "[DRUG DATA DOWNLOADER]: No update for drug data available. Do nothing."
            )
        log.info("[DRUG DATA DOWNLOADER]: Download drug dataset update...")
        drug_loader = await self.importer_class.download_remote_dataset_update()
        log.debug(
            f"[DRUG DATA DOWNLOADER]: Drug dataset update downloaded to {drug_loader.source_dir}."
        )
        drug_loader._ensure_drug_dataset_version()
        log.info(
            "[DRUG DATA DOWNLOADER]: New drug dataset downloaded and registered. Waiting for ingesting worker..."
        )


class TaskDrugDataUpdateDownload(TaskBase):
    async def work(self, source_dir: str = None):
        log.info("Load new drug data if available...")
        drug_data_loader = DrugDataUpdateDownloader()

        await drug_data_loader.download_new_drug_data_update_if_available()
