from typing import List, Mapping, Any
from fastapi import Depends, HTTPException, Security, Response
from itertools import chain

from fastapi import APIRouter, status


from medlogserver.db.user import User
from medlogserver.api.auth.security import (
    user_is_admin,
    get_current_user,
)
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.api.routes.routes_auth import NEEDS_ADMIN_API_INFO
from medlogserver.api.study_access import (
    get_current_user,
)

from medlogserver.model.worker_job import WorkerJobCreate, WorkerJob, WorkerJobState
from medlogserver.db.worker_job import WorkerJobCRUD

from medlogserver.worker.tasks import Tasks

from medlogserver.db.drug_data.drug import DrugCRUD

from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.model.drug_updater_status import DrugUpdaterStatus
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.db.drug_data.drug_dataset_version import DrugDataSetVersionCRUD
from medlogserver.db.drug_data.drug_update_handler.drug_updater_handler import (
    DrugUpdateHandler,
)

from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger(modulename="ROUTER:DRUG_UPDATER")
config = Config()


drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

fast_api_drug_router: APIRouter = APIRouter()

# DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugAPIRead)
fast_api_drug_db_updater_router: APIRouter = APIRouter()


NO_DRUG_UPDATES_IMPLEMENTED_HTTP_EXCEPTION = HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail=f"The current drug database module '{config.DRUG_IMPORTER_PLUGIN}' does not support updates.",
)
extra_responses: Mapping[int, Mapping[str, Any]] = {
    status.HTTP_501_NOT_IMPLEMENTED: {
        "description": "**NOT_IMPLEMENTED Error** - Response when the current drug database module - as configured in `Config`.`DRUG_IMPORTER_PLUGIN`- has the feature 'drug database update' not implemented. "
    },
}


@fast_api_drug_db_updater_router.get(
    "/drug/db/update",
    response_model=DrugUpdaterStatus,
    description="Get some detail about the status of the drug db data",
    responses=extra_responses,
)
async def get_drug_update_status(
    user: User = Security(get_current_user),
    drug_dataset_version_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> DrugUpdaterStatus:
    drug_update_handler = DrugUpdateHandler(user_id=user.id)
    try:
        return await drug_update_handler.get_drug_update_status(
            drug_dataset_version_crud, worker_job_crud
        )
    except NotImplementedError:
        raise NO_DRUG_UPDATES_IMPLEMENTED_HTTP_EXCEPTION


@fast_api_drug_db_updater_router.put(
    "/drug/db/update",
    response_model=DrugUpdaterStatus,
    description="Trigger a new update of the drug database if one is available",
    responses=extra_responses
    | {
        status.HTTP_201_CREATED: {
            "description": "**CREATED** If a new update job was actually started from this trigger call. If there is allready a running update or no update is available, we will just return a 200 status code",
            "content": {"application/json": {"schema": DrugUpdaterStatus.schema()}},
        },
    },
)
async def trigger_drug_update_active(
    response: Response,
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    drug_dataset_version_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> DrugUpdaterStatus:
    if not config.DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB:
        msg = f"The current drug database configuration does not allow manual updates."
        if config.DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB:
            msg = f"\nUpdates will be dont automaticly"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg,
        )
    drug_update_handler = DrugUpdateHandler(user_id=user.id)
    try:
        return await drug_update_handler.trigger_drug_update_active(
            drug_dataset_version_crud=drug_dataset_version_crud,
            worker_job_crud=worker_job_crud,
            http_response=response,
        )
    except NotImplementedError:
        raise NO_DRUG_UPDATES_IMPLEMENTED_HTTP_EXCEPTION
