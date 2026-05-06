from typing import Dict, List, AsyncIterator, Literal, Optional, Self, Type
import uuid

from fastapi import Response, status
from medlogserver.db._session import get_async_session_context
from sqlmodel.ext.asyncio.session import AsyncSession
from medlogserver.model.worker_job import (
    WorkerJob,
    WorkerJobCreate,
    WorkerJobState,
)
from medlogserver.db.worker_job import WorkerJobCRUD, Tasks
from medlogserver.db.drug_data.drug_dataset_version import DrugDataSetVersionCRUD
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_updater_status import DrugUpdaterStatus
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS


from medlogserver.log import get_logger
from medlogserver.config import Config

log = get_logger(modulename="DRUG_UPDATE_HANDLER")
config = Config()
DRUG_IMPORTER_CLASS = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]


class DrugUpdateHandler:
    def __init__(
        self,
        user_id: Optional[uuid.UUID] = None,
    ):
        self.user_id = user_id

    async def get_drug_update_status(
        self,
        drug_dataset_version_crud: DrugDataSetVersionCRUD,
        worker_job_crud: WorkerJobCRUD,
    ) -> DrugUpdaterStatus:
        return await self._get_drug_update_status(
            drug_dataset_version_crud, worker_job_crud
        )

    async def trigger_drug_update_active(
        self,
        drug_dataset_version_crud: DrugDataSetVersionCRUD,
        worker_job_crud: WorkerJobCRUD,
        http_response: Optional[Response] = None,
        parent_job_id: Optional[uuid.UUID] = None,
        extra_job_tags: Optional[List[str]] = None,
    ) -> DrugUpdaterStatus:
        updater_status = await self._get_drug_update_status(
            drug_dataset_version_crud, worker_job_crud
        )
        if updater_status.update_available:
            tags = [
                "drug-data-download",
                f"version:{updater_status.update_available_version}",
            ]
            if parent_job_id:
                tags.extend(
                    [
                        f"triggeredBy:drug-data-auto-updater/version:{updater_status.update_available_version}",
                        f"triggeredByJobID:{parent_job_id}",
                    ]
                )
            if extra_job_tags:
                tags.extend(extra_job_tags)
            data_download_job = WorkerJobCreate(
                task_name=Tasks(Tasks.DRUG_DATA_UPDATE_DOWNLOAD).name,
                task_params=None,
                tags=tags,
                user_id=self.user_id,
            )
            data_download_job = await worker_job_crud.create(data_download_job)
            if http_response:
                http_response.status_code = status.HTTP_201_CREATED
        return await self._get_drug_update_status(
            drug_dataset_version_crud, worker_job_crud
        )

    async def _get_drug_loading_worker_jobs(
        self,
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
            # Exclude jobs that were closed by external events (worker restart or
            # migration cleanup) — these are not real failures and should not
            # bubble up as errors in the status response.
            _INTERRUPTED_TAGS = {"closedByWorkerRestart", "closedByMigration"}
            download_jobs_failed = [
                j for j in download_jobs_failed
                if not _INTERRUPTED_TAGS.intersection(j.tags)
            ]
            loading_jobs_failed = [
                j for j in loading_jobs_failed
                if not _INTERRUPTED_TAGS.intersection(j.tags)
            ]

        return (
            download_jobs_queued
            + download_jobs_running
            + download_jobs_failed
            + loading_jobs_queued
            + loading_jobs_running
            + loading_jobs_failed
        )

    async def _get_drug_update_status(
        self,
        drug_dataset_version_crud: DrugDataSetVersionCRUD,
        worker_job_crud: WorkerJobCRUD,
    ) -> DrugUpdaterStatus:
        # Obtain System Data
        current_drug_dataset = await drug_dataset_version_crud.get_current_active()
        latest_drug_dataset = await drug_dataset_version_crud.get_latest()

        available_update_version = (
            await DRUG_IMPORTER_CLASS().check_for_remote_dataset_update_available()
        )

        current_drug_data_ready_to_use = False
        if current_drug_dataset and current_drug_dataset.import_status == "done":
            current_drug_data_ready_to_use = True

        # generate DrugUpdaterStatus

        active_loading_jobs: List[WorkerJob] = await self._get_drug_loading_worker_jobs(
            worker_job_crud,
            filter_drug_dataset_version_str=available_update_version,
            filter_failed_jobs=False,
        )
        failed_loading_jobs: List[WorkerJob] = await self._get_drug_loading_worker_jobs(
            worker_job_crud,
            filter_drug_dataset_version_str=available_update_version,
            filter_failed_jobs=True,
        )
        last_error: str | None = None
        if failed_loading_jobs:
            last_error = failed_loading_jobs[0].last_error

        log.debug(
            f"\n\n_get_drug_update_status active_loading_jobs {active_loading_jobs}\navailable_update_version: {available_update_version}\n"
        )
        log.debug(
            f"\n\n_get_drug_update_status active_loading_jobs {active_loading_jobs}\navailable_update_version: {available_update_version}\n"
        )

        update_running = True if active_loading_jobs else False

        if active_loading_jobs and available_update_version:
            version_tag = next(
                (t for t in active_loading_jobs[0].tags if t.startswith("version:")),
                None,
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
