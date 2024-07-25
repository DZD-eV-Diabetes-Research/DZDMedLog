from medlogserver.worker.tasks.provisioning_data_loader import load_provisioning_data
from medlogserver.worker.tasks.refresh_token_cleaner import clean_tokens
from medlogserver.worker.tasks.wido_gkv_arzneimittelindex_importer import (
    import_wido_gkv_arzneimittelindex_data,
)
from medlogserver.worker.tasks.export_study_data import export_study_intake_data
from enum import Enum


class Tasks(str, Enum):
    LOAD_PROVISIONING_DATA = load_provisioning_data
    CLEAN_TOKENS = clean_tokens
    IMPORT_WIDO_GKV_ARZNEIMITTELINDEX_DATA = import_wido_gkv_arzneimittelindex_data
    EXPORT_STUDY_INTAKES = export_study_intake_data
