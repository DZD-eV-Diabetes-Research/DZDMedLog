from fastapi import (
    Depends,
    Security,
)


from fastapi import APIRouter

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
    update_version = (
        await drug_importer_class().check_for_remote_dataset_update_available()
    )
    download_jobs_queued = await worker_job_crud.list(
        filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
        filter_job_state=WorkerJobState.QUEUED,
    )
    download_jobs_running = await worker_job_crud.list(
        filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
        filter_job_state=WorkerJobState.RUNNING,
    )

    last_update_run_error = None
    last_update_run_datetime_utc = None
    update_running = False
    if latest_drug_dataset:
        print(f"version:{latest_drug_dataset.dataset_version}")
        download_jobs_failed = await worker_job_crud.list(
            filter_task=Tasks.DRUG_DATA_UPDATE_DOWNLOAD,
            filter_job_state=WorkerJobState.FAILED,
            filter_tags=[
                f"version:{update_version}",
            ],
        )
        print("download_jobs_failed:", download_jobs_failed)
        if download_jobs_failed:
            last_update_run_error = download_jobs_failed[0].last_error
        last_update_run_datetime_utc = latest_drug_dataset.import_end_datetime_utc
        if latest_drug_dataset.import_error:
            last_update_run_error = latest_drug_dataset.import_error

        if latest_drug_dataset.import_status in ["queued", "running"]:
            update_running = True
    if download_jobs_queued or download_jobs_running:
        update_running = True

    if update_running is False:
        loading_jobs_queued = await worker_job_crud.list(
            filter_task=Tasks.LOAD_DRUG_DATA,
            filter_job_state=WorkerJobState.QUEUED,
            filter_tags=[
                f"version:{update_version}",
            ],
        )
        if loading_jobs_queued:
            update_running = True
    if update_running is False:
        loading_jobs_running = await worker_job_crud.list(
            filter_task=Tasks.LOAD_DRUG_DATA,
            filter_job_state=WorkerJobState.RUNNING,
            filter_tags=[
                f"version:{update_version}",
            ],
        )
        if loading_jobs_running:
            update_running = True
    loading_jobs_failed = await worker_job_crud.list(
        filter_task=Tasks.LOAD_DRUG_DATA,
        filter_job_state=WorkerJobState.FAILED,
        filter_tags=[
            f"version:{update_version}",
        ],
    )
    if loading_jobs_failed:
        last_update_run_error = loading_jobs_failed[0].last_error

    current_drug_data_ready_to_use = False
    if current_drug_dataset and current_drug_dataset.import_status == "done":
        current_drug_data_ready_to_use = True

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
    update_version = (
        await drug_importer_class().check_for_remote_dataset_update_available()
    )
    if update_version:
        data_download_job = WorkerJobCreate(
            task_name=Tasks(Tasks.DRUG_DATA_UPDATE_DOWNLOAD).name,
            task_params=None,
            tags=["drug-data-download", f"version:{update_version}"],
            user_id=user.id,
        )
        data_download_job = await worker_job_crud.create(data_download_job)

    return await _get_drug_update_status(drug_dataset_version_crud, worker_job_crud)
