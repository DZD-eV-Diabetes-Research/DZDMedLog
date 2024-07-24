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

import enum
from fastapi import Depends, APIRouter

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


class ExportJob(BaseModel):
    export_id: uuid.UUID
    state: WorkerJobState
    download_file_path: str


@fast_api_export_router.get(
    "/study/{study_id}/export",
    response_model=PaginatedResponse[WorkerJob],
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
        filter_tags=["export", study_access.study.id],
        filter_job_state=filter_job_state,
        pagination=pagination,
    )
    total_count = worker_job_crud.count(
        filter_user_id=current_user.id,
        filter_tags=["export", study_access.study.id],
        filter_job_state=filter_job_state,
        pagination=pagination,
    )
    export_jobs: List[ExportJob] = []
    for job in result_items:
        export_jobs.append(
            ExportJob(export_id=job.id, state=job.state, download_file_path=job.result)
        )
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
    format: Literal["csv", "json"] = "csv",
    current_user: User = Depends(get_current_user),
    study_access: UserStudyAccess = Security(user_has_study_access),
    worker_job_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> ExportJob:
    # you are here
    pass


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
    pass
