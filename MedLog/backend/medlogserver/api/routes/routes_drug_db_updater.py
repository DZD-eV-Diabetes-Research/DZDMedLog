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


from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger(modulename="ROUTER:DRUG_UPDATER")
config = Config()


drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

fast_api_drug_router: APIRouter = APIRouter()

# DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugAPIRead)
fast_api_drug_db_updater_router: APIRouter = APIRouter()


async def _get_drug_loading_worker_jobs(
    worker_job_crud: WorkerJobCRUD,
    filter_drug_dataset_version_str: str | None = None,
    filter_failed_jobs: bool | None = None,
) -> List[WorkerJob]:
    download_jobs_queued: List[WorkerJob] = []
    download_jobs_running: List[WorkerJob] = []
    download_jobs_failed: List[WorkerJob] = []

    loading_jobs_queued: List[WorkerJob] = []
    loading_jobs_running: List[WorkerJob] = []
    loading_jobs_failed: List[WorkerJob] = []
    log.debug(
        f"_get_drug_loading_worker_jobs filter_drug_dataset_version_str {filter_drug_dataset_version_str}"
    )
    if filter_failed_jobs != True:
        download_jobs_queued = await worker_job_crud.list(
            filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
            filter_job_state=WorkerJobState.QUEUED,
            filter_tags=[
                f"version:{filter_drug_dataset_version_str}",
            ]
            if filter_drug_dataset_version_str
            else None,
        )

        download_jobs_running = list(
            await worker_job_crud.list(
                filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
                filter_job_state=WorkerJobState.RUNNING,
                filter_tags=[
                    f"version:{filter_drug_dataset_version_str}",
                ]
                if filter_drug_dataset_version_str
                else None,
            )
        )
        loading_jobs_queued = list(
            await worker_job_crud.list(
                filter_task=Tasks.DRUG_DATA_LOAD,
                filter_job_state=WorkerJobState.QUEUED,
                filter_tags=[
                    f"version:{filter_drug_dataset_version_str}",
                ]
                if filter_drug_dataset_version_str
                else None,
            )
        )
        loading_jobs_running = list(
            await worker_job_crud.list(
                filter_task=Tasks.DRUG_DATA_LOAD,
                filter_job_state=WorkerJobState.RUNNING,
                filter_tags=[
                    f"version:{filter_drug_dataset_version_str}",
                ]
                if filter_drug_dataset_version_str
                else None,
            )
        )

    if filter_failed_jobs != False:
        download_jobs_failed = list(
            await worker_job_crud.list(
                filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
                filter_job_state=WorkerJobState.FAILED,
                filter_tags=[
                    f"version:{filter_drug_dataset_version_str}",
                ]
                if filter_drug_dataset_version_str
                else None,
            )
        )

        loading_jobs_failed = list(
            await worker_job_crud.list(
                filter_task=Tasks.DRUG_DATA_LOAD,
                filter_job_state=WorkerJobState.FAILED,
                filter_tags=[
                    f"version:{filter_drug_dataset_version_str}",
                ]
                if filter_drug_dataset_version_str
                else None,
            )
        )

    return (
        download_jobs_queued
        + download_jobs_running
        + download_jobs_failed
        + loading_jobs_queued
        + loading_jobs_running
        + loading_jobs_failed
    )


async def _get_drug_update_status(
    drug_dataset_version_crud: DrugDataSetVersionCRUD, worker_job_crud: WorkerJobCRUD
) -> DrugUpdaterStatus:
    # Obtain System Data
    current_drug_dataset = await drug_dataset_version_crud.get_current_active()
    latest_drug_dataset = await drug_dataset_version_crud.get_latest()

    available_update_version = (
        await drug_importer_class().check_for_remote_dataset_update_available()
    )

    current_drug_data_ready_to_use = False
    if current_drug_dataset and current_drug_dataset.import_status == "done":
        current_drug_data_ready_to_use = True

    # generate DrugUpdaterStatus

    active_loading_jobs: List[WorkerJob] = await _get_drug_loading_worker_jobs(
        worker_job_crud,
        filter_drug_dataset_version_str=available_update_version,
        filter_failed_jobs=False,
    )
    failed_loading_jobs: List[WorkerJob] = await _get_drug_loading_worker_jobs(
        worker_job_crud,
        filter_drug_dataset_version_str=available_update_version,
        filter_failed_jobs=True,
    )
    last_error: str | None = None
    if failed_loading_jobs:
        last_error = (
            failed_loading_jobs[0].last_error or failed_loading_jobs[0].last_error
        )

    log.debug(
        f"\n\n_get_drug_update_status active_loading_jobs {active_loading_jobs}\navailable_update_version: {available_update_version}\n"
    )
    log.debug(
        f"\n\n_get_drug_update_status active_loading_jobs {active_loading_jobs}\navailable_update_version: {available_update_version}\n"
    )

    update_running = True if active_loading_jobs else False

    if active_loading_jobs and available_update_version:
        version_tag = next(
            (t for t in active_loading_jobs[0].tags if t.startswith("version:")), None
        )
        if version_tag and available_update_version in version_tag:
            # if the update is allready running we wont show it as available to prevent multiple start up tries of the update
            available_update_version = None
    update_available = True if available_update_version else False

    return DrugUpdaterStatus(
        update_available=update_available,
        update_available_version=available_update_version,
        update_running=update_running,
        update_running_version=available_update_version if update_running else None,
        last_update_run_datetime_utc=latest_drug_dataset.import_end_datetime_utc
        if latest_drug_dataset
        else None,
        last_update_run_error=last_error,
        current_drug_data_version=current_drug_dataset.dataset_version
        if current_drug_dataset
        else None,
        current_drug_data_ready_to_use=current_drug_data_ready_to_use,
    )

    return DrugUpdaterStatus(
        update_available=False,
        update_available_version=None,
        update_running=False,
        update_running_version=None,
        last_update_run_datetime_utc=latest_drug_dataset.import_end_datetime_utc
        if latest_drug_dataset
        else None,
        last_update_run_error=None,
        current_drug_data_version=current_drug_dataset.dataset_version
        if current_drug_dataset
        else None,
        current_drug_data_ready_to_use=current_drug_data_ready_to_use,
    )


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
    try:
        return await _get_drug_update_status(drug_dataset_version_crud, worker_job_crud)
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
    try:
        updater_status = await _get_drug_update_status(
            drug_dataset_version_crud, worker_job_crud
        )
        if updater_status.update_available:
            data_download_job = WorkerJobCreate(
                task_name=Tasks(Tasks.DRUG_DATA_UPDATE_DOWNLOAD).name,
                task_params=None,
                tags=[
                    "drug-data-download",
                    f"version:{updater_status.update_available_version}",
                ],
                user_id=user.id,
            )
            data_download_job = await worker_job_crud.create(data_download_job)
            response.status_code = status.HTTP_201_CREATED
        return await _get_drug_update_status(drug_dataset_version_crud, worker_job_crud)
    except NotImplementedError:
        raise NO_DRUG_UPDATES_IMPLEMENTED_HTTP_EXCEPTION
