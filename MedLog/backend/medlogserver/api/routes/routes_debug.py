from typing import Annotated, Sequence, List, Type, Optional
from datetime import datetime, timedelta, timezone
from pydantic.json_schema import SkipJsonSchema
from uuid import UUID
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
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.worker_job import WorkerJob
from medlogserver.db.worker_job import WorkerJobCRUD, Tasks, WorkerJobState
from medlogserver.config import Config
from medlogserver.log import get_logger

config = Config()
log = get_logger()

drug_importer_class: Type[DrugDataSetImporterBase] = DRUG_IMPORTERS[
    config.DRUG_IMPORTER_PLUGIN
]

fast_api_debug_router: APIRouter = APIRouter()


@fast_api_debug_router.get(
    "/debug/worker/job",
    response_model=List[WorkerJob],
    description="List all background worker jobs that are registered in the database. DZDMedLog server must be set to `LOG_LEVEL=DEBUG` for this endpoint to work. Also user must be admin.",
)
async def list_all_worker_jobs(
    filter_tags: Annotated[
        List[str] | SkipJsonSchema[None], Query()
    ] = None,  # List of string is broken in the api browser. There seems to be a fix (https://github.com/fastapi/fastapi/discussions/11494) with `SkipJsonSchema`but it does not work in this case
    filter_user_id: Optional[UUID] = None,
    filter_job_state: Optional[WorkerJobState] = None,
    filter_intervalled_job: Optional[bool] = None,
    filter_task: Optional[Tasks | str] = None,
    is_admin: User = Security(user_is_admin),
    drug_dataset_version_crud: WorkerJobCRUD = Depends(WorkerJobCRUD.get_crud),
) -> List[WorkerJob]:
    if config.LOG_LEVEL != "DEBUG":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Job is listing of server-worker only enabled in DEBUG mode.",
        )
    return list(
        await drug_dataset_version_crud.list(
            filter_user_id=filter_user_id,
            filter_intervalled_job=filter_intervalled_job,
            filter_tags=filter_tags,
            filter_job_state=filter_job_state,
            filter_task=filter_task,
        )
    )
