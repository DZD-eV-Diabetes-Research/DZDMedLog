from typing import List, Dict, Type, Callable, Optional, Tuple
import importlib
import uuid
from pathlib import Path, PurePath
from dataclasses import dataclass
import yaml
import traceback

# internal imports
from medlogserver.worker.task import TaskBase

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db._session import get_async_session_context
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.db.drug_data.drug_update_handler.drug_updater_handler import (
    DrugUpdateHandler,
)

from medlogserver.model.worker_job import WorkerJobCreate, WorkerJob, WorkerJobState
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.worker.tasks import Tasks

from medlogserver.db.drug_data.drug_dataset_version import (
    DrugDataSetVersionCRUD,
    DrugDataSetVersion,
)
from medlogserver.api.paginator import QueryParamsInterface, create_query_params_class

log = get_logger(modulename="Task:DrugDataAutoUpdater")
config = Config()


class DrugDataAutoUpdater:
    async def trigger_update(self, parent_job_id: uuid.UUID):
        drug_update_handler = DrugUpdateHandler(user_id=None)
        async with get_async_session_context() as session:
            async with (
                DrugDataSetVersionCRUD.crud_context(
                    session
                ) as drug_dataset_version_crud,
                WorkerJobCRUD.crud_context(session) as worker_job_crud,
            ):
                try:
                    return await drug_update_handler.trigger_drug_update_active(
                        drug_dataset_version_crud=drug_dataset_version_crud,
                        worker_job_crud=worker_job_crud,
                        parent_job_id=parent_job_id,
                    )
                except NotImplementedError:
                    log.error(
                        f"Auto updating is enabled but the current drug importer `{config.DRUG_IMPORTER_PLUGIN}` module does not support auto updating."
                    )


class TaskDrugDataAutoUpdater(TaskBase):
    async def work(self):
        if config.DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB:
            log.info("Start checking if new drug update is available...")
            drug_auto_uploader = DrugDataAutoUpdater()

            await drug_auto_uploader.trigger_update(parent_job_id=self.job.id)
        else:
            log.info(
                f"Skip drug database auto update because `config.DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB`:{config.DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB}"
            )
