from typing import Annotated, Sequence, List, Type
from datetime import datetime, timedelta, timezone


from fastapi import (
    Depends,
    Security,
    HTTPException,
    status,
    Query,
    Body,
    Form,
    Path,
    Response,
)

from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from fastapi import Depends, APIRouter


from medlogserver.db.user import User


from medlogserver.utils import get_app_version, get_version_git_branch_name

from medlogserver.model.app_version import AppVersion
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.api.auth.security import get_logged_in_state
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.branding_data import BrandingData
from medlogserver.model.drug_data_config import DrugDataConfig
from medlogserver.model.api_only.system_accouncement import SystemAnnouncement
from medlogserver.config import Config
from medlogserver.log import get_logger

config = Config()
log = get_logger()

drug_importer_class: Type[DrugDataSetImporterBase] = DRUG_IMPORTERS[
    config.DRUG_IMPORTER_PLUGIN
]

fast_api_config_router: APIRouter = APIRouter()


@fast_api_config_router.get(
    "/config/version",
    response_model=AppVersion,
    description="Get the basic health state of the system.",
)
async def get_version() -> AppVersion:
    return AppVersion(version=get_app_version(), branch=get_version_git_branch_name())


@fast_api_config_router.get(
    "/config/branding",
    response_model=BrandingData,
    description="Provides some branding data like support email address.",
)
async def get_branding_data() -> BrandingData:
    return BrandingData(support_email=config.BRANDING_SUPPORT_EMAIL_ADDRESS)


@fast_api_config_router.get(
    "/config/drugdata",
    response_model=DrugDataConfig,
    description="Provides some meta data about the drug data configuration",
)
async def get_drug_data_config() -> DrugDataConfig:
    drug_importer_dummy = drug_importer_class()
    return DrugDataConfig(
        drug_data_source_name=drug_importer_dummy.dataset_name,
        drug_data_source_info_url=drug_importer_dummy.dataset_link,
        supports_force_manual_update=config.DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB
        and drug_importer_dummy.capabilities.can_be_triggered_for_manual_update,
        supports_scheduled_auto_update=config.DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB
        and drug_importer_dummy.capabilities.can_download_remote_updates
        and drug_importer_dummy.capabilities.can_check_for_remote_updates,
    )


@fast_api_config_router.get(
    "/config/announcements",
    response_model=List[SystemAnnouncement],
    description="Provides some meta data about the drug data configuration",
)
async def get_system_announcements(
    user_is_logged_in_state: User = Security(get_logged_in_state),
) -> List[SystemAnnouncement]:
    all_announcements: List[SystemAnnouncement] = []
    log.debug(f"config.SYSTEM_ANNOUNCEMENTS: {config.SYSTEM_ANNOUNCEMENTS}")
    for announcement in config.SYSTEM_ANNOUNCEMENTS:
        if not user_is_logged_in_state and not announcement.public:
            continue
        all_announcements.append(
            SystemAnnouncement(
                id=str(hash(f"{announcement.type} {announcement.message}")),
                type=announcement.type,
                message=announcement.message,
            )
        )
    return all_announcements
