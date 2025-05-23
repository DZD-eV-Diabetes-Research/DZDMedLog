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
from medlogserver.worker.tasks import Tasks
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.db.user import User
from medlogserver.db.user_auth import UserAuthCRUD

from medlogserver.model.worker_job import WorkerJobCreate, WorkerJob, WorkerJobState
from medlogserver.db.worker_job import WorkerJobCRUD

from medlogserver.config import Config
from medlogserver.api.study_access import (
    user_has_study_access,
    UserStudyAccess,
)
from medlogserver.utils import sanitize_string, http_exception_to_resp_desc
from medlogserver.db.study import StudyCRUD
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_export_router: APIRouter = APIRouter()


exception_export_job_not_existing = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Export job does not exist.",
)

exception_export_job_not_finished = HTTPException(
    status_code=status.HTTP_425_TOO_EARLY,
    detail="Export job is not finished yet. Try again later.",
)


class ExportJob(BaseModel):
    export_id: uuid.UUID
    state: WorkerJobState
    download_file_path: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None
    export_format: Literal["csv", "json"] = None

    @classmethod
    def from_worker_job(cls, job: WorkerJob):
        export_job = ExportJob(
            export_id=job.id,
            state=job.get_state(),
            created_at=job.created_at,
            export_format=job.task_params["format_"],
        )
        if job.get_state() == WorkerJobState.SUCCESS:
            export_job.download_file_path = (
                f"study/{job.task_params['study_id']}/export/{job.id}/download"
            )
        return export_job


ExportJobQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    ExportJob, default_order_by_attr="created_at"
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
    pagination: QueryParamsInterface = Depends(ExportJobQueryParams),
) -> PaginatedResponse[ExportJob]:
    result_items = await worker_job_crud.list(
        filter_user_id=current_user.id,
        filter_tags=["export", str(study_access.study.id)],
        filter_job_state=filter_job_state,
        pagination=pagination,
    )
    total_count = await worker_job_crud.count(
        filter_user_id=current_user.id,
        filter_tags=["export", str(study_access.study.id)],
        filter_job_state=filter_job_state,
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
        user_id=current_user.id,
        task_name=Tasks(Tasks.EXPORT_STUDY_INTAKES).name,
        task_params={
            "study_id": str(study_access.study.id),
            "format_": format,
        },
        tags=["export", str(study_access.study.id)],
    )
    system_job = await worker_job_crud.create(system_job)
    return ExportJob.from_worker_job(system_job)


@fast_api_export_router.get(
    "/study/{study_id}/export/{export_job_id}",
    response_model=ExportJob,
    description=f"Get an existing export. This endpoint can be used to get the state or result download path",
    responses={
        **http_exception_to_resp_desc(exception_export_job_not_existing),
    },
)
async def get_export(
    export_job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> ExportJob:

    worker_job: WorkerJob = await worker_job_crud.get(
        export_job_id, raise_exception_if_none=exception_export_job_not_existing
    )
    if worker_job.user_id != current_user.id:
        # user had a existing export job id but the job actually belongs to another user
        # there is something fishy going on...
        # lets log this and return a 404
        log.warning(
            f"User '{current_user.user_name}' requested job with id '{export_job_id}' which belongs to another user. Access was denied, but maybe something fishy is ging on here..."
        )
        raise exception_export_job_not_existing

    return ExportJob.from_worker_job(worker_job)


@fast_api_export_router.get(
    "/study/{study_id}/export/{export_job_id}/download",
    response_class=FileResponse,
    description=f"Download the export. Job muste be in state `SUCCESS`",
    responses={
        **http_exception_to_resp_desc(exception_export_job_not_finished),
        **http_exception_to_resp_desc(exception_export_job_not_existing),
    },
)
async def download_export(
    export_job_id: uuid.UUID,
    study_id: uuid.UUID,
    # current_user: User = Depends(get_current_user),
    # study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
) -> FileResponse:
    worker_job: WorkerJob = await worker_job_crud.get(
        export_job_id, raise_exception_if_none=exception_export_job_not_existing
    )
    export_job = ExportJob.from_worker_job(worker_job)
    if export_job.download_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail="Export job is not finished.",
        )
    """
    if worker_job.user_id != current_user.id:
        # user had a existing export job id but the job actually belongs to another user
        # there is something fishy going on...
        # lets log this and return a 404
        log.warning(
            f"User '{current_user.user_name}' requested job with id '{export_job_id}' which belongs to another user. Access was denied, but maybe something fishy is ging on here..."
        )
        raise exception_job_not_existing
    """
    study = await study_crud.get(study_id=study_id)
    media_type = (
        "text/csv" if worker_job.task_params["format_"] == "csv" else "application/json"
    )
    filename = f"""medlog_export_{sanitize_string(study.display_name,replace_space_with="-")}_{worker_job.run_started_at.strftime('%S-%M-%H_%d-%m-%Y')}.{worker_job.task_params['format_']}"""
    # headers = {"Content-Disposition": f'''attachment; filename="{filename}"'''}
    # headers["Content-Type"] = media_type
    return FileResponse(
        path=worker_job.last_result,
        # headers=headers,
        filename=filename,
        media_type=media_type,
    )
