from typing import TYPE_CHECKING, Type
from enum import Enum
import importlib
from pathlib import Path

if TYPE_CHECKING:
    from medlogserver.worker.task import TaskBase


# ToDo: We need to do import at runtime based on the class path, otherwise i get an circular import error... i hate this. Review later...
class Tasks(Enum):
    LOAD_PROVISIONING_DATA = (
        "medlogserver.worker.tasks.provisioning_data_loader.TaskLoadProvisioningData"
    )
    CLEAN_TOKENS = "medlogserver.worker.tasks.refresh_token_cleaner.TaskCleanTokens"
    EXPORT_STUDY_INTAKES = (
        "medlogserver.worker.tasks.export_study_data.TaskExportStudyIntakeData"
    )
    RUN_ADHOC_JOBS = "medlogserver.worker.tasks.run_ad_hoc_jobs.TaskRunAdHocJobs"
    LOAD_DRUG_DATA = "medlogserver.worker.tasks.drug_data_load.TaskDrugDataLoading"
    DRUG_DATA_UPDATE_DOWNLOAD = (
        "medlogserver.worker.tasks.drug_data_update_download.TaskDrugDataUpdateDownload"
    )
    DRUG_DATA_CLEANING = "medlogserver.worker.tasks.drug_data_remove_obsolete_drug_entries.TaskRemoveOnbsoleteDrugDataEntries"


def import_task_class(class_path: str) -> Type["TaskBase"]:
    module = importlib.import_module(Path(class_path).stem)
    return getattr(module, Path(class_path).suffix.lstrip("."))
