from enum import Enum
from medlogserver.worker.tasks.provisioning_data_loader import TaskLoadProvisioningData
from medlogserver.worker.tasks.refresh_token_cleaner import TaskCleanTokens
from medlogserver.worker.tasks.wido_gkv_arzneimittelindex_importer import (
    TaskImportGKVArnzeimittelIndexData,
)
from medlogserver.worker.tasks.export_study_data import TaskExportStudyIntakeData
from medlogserver.worker.tasks.run_ad_hoc_jobs import TaskRunAdHocJobs


class Tasks(Enum):
    LOAD_PROVISIONING_DATA = TaskLoadProvisioningData
    CLEAN_TOKENS = TaskCleanTokens
    IMPORT_WIDO_GKV_ARZNEIMITTELINDEX_DATA = TaskImportGKVArnzeimittelIndexData
    EXPORT_STUDY_INTAKES = TaskExportStudyIntakeData
    RUN_ADHOC_JOBS = TaskRunAdHocJobs
