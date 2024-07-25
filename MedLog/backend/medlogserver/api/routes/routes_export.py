from typing import Annotated, Sequence, List, Type, Optional, Literal
from datetime import datetime, timedelta, timezone
import uuid
from pydantic import BaseModel
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
from fastapi.responses import FileResponse

import enum
from fastapi import Depends, APIRouter
from medlogserver.worker import Tasks
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.db.user import User
from medlogserver.db.user_auth import UserAuthCRUD

from medlogserver.model.worker_job import WorkerJobCreate, WorkerJob, WorkerJobState
from medlogserver.worker.ad_hoc_job_runner import WorkerAdHocJobRunner
from medlogserver.db.worker_job import WorkerJobCRUD

from medlogserver.config import Config
from medlogserver.api.study_access import (
    user_has_study_access,
    UserStudyAccess,
)
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_export_router: APIRouter = APIRouter()

WorkerJobQueryParams: Type[QueryParamsInterface] = create_query_params_class(WorkerJob)

exception_job_not_existing = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Export job does not exist.",
)


class ExportJob(BaseModel):
    export_id: uuid.UUID
    state: WorkerJobState
    download_file_path: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None

    @classmethod
    def from_worker_job(cls, job: WorkerJob):
        return ExportJob(
            export_id=job.id,
            state=job.state,
            created_at=job.created_at,
        )


@fast_api_export_router.get(
    "/study/{study_id}/export",
    response_model=PaginatedResponse[ExportJob],
    description=f"List export jobs.",
)
async def list_export_jobs(
    filter_job_state: Optional[WorkerJobState] = Query(None),
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(WorkerJobQueryParams),
) -> PaginatedResponse[ExportJob]:
    result_items = await worker_job_crud.list(
        filter_user_id=current_user.id,
        filter_tags=["export", str(study_access.study.id)],
        filter_job_state=filter_job_state,
        pagination=pagination,
    )
    total_count = worker_job_crud.count(
        filter_user_id=current_user.id,
        filter_tags=["export", str(study_access.study.id)],
        filter_job_state=filter_job_state,
        pagination=pagination,
    )
    export_jobs: List[ExportJob] = []
    for job in result_items:
        export_jobs.append(ExportJob.from_worker_job(job))
    return PaginatedResponse(
        total_count=total_count,
        offset=pagination.offset,
        count=len(export_jobs),
        items=export_jobs,
    )


@fast_api_export_router.post(
    "/study/{study_id}/export",
    response_model=ExportJob,
    description=f"Create a new export job. This will start a process in the background, which creates a export file. With the ID of the response model (ExportJob) you can query the state and later download the result files.",
)
async def create_export(
    format: Annotated[Literal["csv", "json"], Query()] = "csv",
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> ExportJob:
    job_id = uuid.uuid4()
    system_job = WorkerJobCreate(
        id=job_id,
        task=Tasks.EXPORT_STUDY_INTAKES,
        params={
            "study_id": str(study_access.study.id),
            "format": format,
            "job_id": job_id,
        },
        tags=["export", str(study_access.study.id)],
    )
    system_job = await worker_job_crud.create(system_job)
    return ExportJob.from_worker_job(system_job)


@fast_api_export_router.get(
    "/study/{study_id}/export/{export_job_id}",
    response_model=ExportJob,
    description=f"Get an existing export. This endpoint can be used to get the state or result download path",
)
async def get_export(
    export_job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> ExportJob:

    worker_job: WorkerJob = await worker_job_crud.get(
        export_job_id, raise_exception_if_none=exception_job_not_existing
    )
    if worker_job.user_id != current_user.id:
        # user had a existing export job id but the job actually belongs to another user
        # there is something fishy going on...
        # lets log this and return a 404
        log.warning(
            f"User '{current_user.user_name}' requested job with id '{export_job_id}' which belongs to another user. Access was denied, but maybe something fishy is ging on here..."
        )
        raise exception_job_not_existing

    export_job = ExportJob.from_worker_job(worker_job)
    if worker_job.state == WorkerJobState.SUCCESS:
        export_job.download_file_path = (
            f"study/{study_access.study.id}/export/{export_job_id}/download"
        )


@fast_api_export_router.get(
    "/study/{study_id}/export/{export_job_id}/download",
    response_class=FileResponse,
    description=f"Download the export. Job muste be in state `SUCCESS`",
)
async def download_export(
    export_job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> FileResponse:
    worker_job: WorkerJob = await worker_job_crud.get(
        export_job_id, raise_exception_if_none=exception_job_not_existing
    )
    if worker_job.user_id != current_user.id:
        # user had a existing export job id but the job actually belongs to another user
        # there is something fishy going on...
        # lets log this and return a 404
        log.warning(
            f"User '{current_user.user_name}' requested job with id '{export_job_id}' which belongs to another user. Access was denied, but maybe something fishy is ging on here..."
        )
        raise exception_job_not_existing
    FileResponse(path=worker_job.result,headers=,media_type=,filename=,content_disposition_type=)
    return FileResponse(worker_job.result)
