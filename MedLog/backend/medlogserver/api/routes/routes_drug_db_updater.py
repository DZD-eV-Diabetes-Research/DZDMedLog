from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn, Type, Optional
import uuid
from fastapi import (
    Depends,
    Security,
    FastAPI,
    HTTPException,
    status,
    Query,
    Body,
    Form,
    Path,
    Response,
    status,
)
from itertools import chain
import asyncio
from pydantic import BaseModel, Field, create_model
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.db.user import User
from medlogserver.utils import run_async_sync
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.api.routes.routes_auth import NEEDS_ADMIN_API_INFO
from medlogserver.api.study_access import (
    get_current_user,
)
from medlogserver.model.unset import Unset
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


from medlogserver.config import Config

config = Config()

drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

fast_api_drug_router: APIRouter = APIRouter()

# DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugAPIRead)
fast_api_drug_db_updater_router: APIRouter = APIRouter()


async def _get_drug_update_status(
    drug_dataset_version_crud: DrugDataSetVersionCRUD, worker_job_crud: WorkerJobCRUD
) -> DrugUpdaterStatus:
    current_drug_dataset = await drug_dataset_version_crud.get_current_active()
    latest_drug_dataset = await drug_dataset_version_crud.get_latest()
    download_jobs_queued = worker_job_crud.list(
        filter_job_state=WorkerJobState.QUEUED, filter_tags=["drug-data-download"]
    )
    download_jobs_running = worker_job_crud.list(
        filter_job_state=WorkerJobState.RUNNING, filter_tags=["drug-data-download"]
    )
    last_update_run_error = None
    last_update_run_datetime_utc = None
    update_running = False
    if latest_drug_dataset:
        last_update_run_datetime_utc = latest_drug_dataset.import_end_datetime_utc
        if latest_drug_dataset.import_error:
            last_update_run_error = latest_drug_dataset.import_error
        if latest_drug_dataset.import_status in ["queued", "running"]:
            update_running = True
    if download_jobs_queued or download_jobs_running:
        update_running = True

    current_drug_data_ready_to_use = False
    if current_drug_dataset and current_drug_dataset.import_status == "done":
        current_drug_data_ready_to_use = True
    update_version = (
        await drug_importer_class.check_for_remote_dataset_update_available()
    )
    return DrugUpdaterStatus(
        update_available=True
        if update_version
        else False,  # Todo: Query the drug db module for available updates
        update_available_version=update_version,
        update_running=update_running,
        last_update_run_datetime_utc=last_update_run_datetime_utc,
        last_update_run_error=last_update_run_error,
        current_drug_data_version=current_drug_dataset.dataset_version
        if current_drug_dataset
        else None,
        current_drug_data_ready_to_use=current_drug_data_ready_to_use,
    )


@fast_api_drug_db_updater_router.get(
    "/drug/db/update",
    response_model=DrugUpdaterStatus,
    description="Get some detail about the status of the drug db data",
)
async def get_drug_update_status(
    user: User = Security(get_current_user),
    drug_dataset_version_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> DrugUpdaterStatus:
    return await _get_drug_update_status(drug_dataset_version_crud, worker_job_crud)


@fast_api_drug_db_updater_router.put(
    "/drug/db/update",
    response_model=DrugUpdaterStatus,
    description="Trigger a new update of the drug database if one is available",
)
async def trigger_drug_update_active(
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    drug_dataset_version_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> DrugUpdaterStatus:
    update_version = drug_importer_class.check_for_remote_dataset_update_available()
    if update_version:
        data_download_job = WorkerJobCreate(
            task_name=Tasks(Tasks.DRUG_DATA_UPDATE_DOWNLOAD).name,
            task_params=None,
            tags=["drug-data-download"],
        )
        data_download_job = await worker_job_crud.create(data_download_job)

    return await _get_drug_update_status(drug_dataset_version_crud, worker_job_crud)
