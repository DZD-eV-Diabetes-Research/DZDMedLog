from enum import Enum

"""
from medlogserver.worker.tasks.provisioning_data_loader import TaskLoadProvisioningData
from medlogserver.worker.tasks.refresh_token_cleaner import TaskCleanTokens
from medlogserver.worker.tasks.wido_gkv_arzneimittelindex_importer import (
    TaskImportGKVArnzeimittelIndexData,
)
from medlogserver.worker.tasks.export_study_data import TaskExportStudyIntakeData
from medlogserver.worker.tasks.run_ad_hoc_jobs import TaskRunAdHocJobs
"""


# ToDo: We need to do import at runtime based on the class path, otherwise i get an circular import error... i hate this. Review later...
class Tasks(Enum):
    LOAD_PROVISIONING_DATA = (
        "medlogserver.worker.tasks.provisioning_data_loader.TaskLoadProvisioningData"
    )
    CLEAN_TOKENS = "medlogserver.worker.tasks.refresh_token_cleaner.TaskCleanTokens"
    IMPORT_WIDO_GKV_ARZNEIMITTELINDEX_DATA = "medlogserver.worker.tasks.wido_gkv_arzneimittelindex_importer.TaskImportGKVArnzeimittelIndexData"
    EXPORT_STUDY_INTAKES = (
        "medlogserver.worker.tasks.export_study_data.TaskExportStudyIntakeData"
    )
    RUN_ADHOC_JOBS = "medlogserver.worker.tasks.run_ad_hoc_jobs.TaskRunAdHocJobs"


# hacky helper class
import importlib
from pathlib import Path
from medlogserver.worker.task import TaskBase
from typing import Type


def import_task_class(class_path: str) -> Type[TaskBase]:
    module = importlib.import_module(Path(class_path).stem)
    return getattr(module, Path(class_path).suffix.lstrip("."))
