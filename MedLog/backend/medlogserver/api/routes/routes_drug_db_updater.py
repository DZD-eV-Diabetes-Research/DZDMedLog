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
from medlogserver.api.routes.routes_auth import NEEDS_ADMIN_API_INFO
from medlogserver.api.study_access import (
    get_current_user,
)
from medlogserver.model.unset import Unset

from medlogserver.config import Config


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

# DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugAPIRead)
fast_api_drug_db_updater_router: APIRouter = APIRouter()


@fast_api_drug_db_updater_router.get(
    "/drug/db/update",
    response_model=DrugUpdaterStatus,
    description=f"Get some detail about the status of the drug db data",
)
async def get_drug_update_status(
    user: User = Security(get_current_user),
    drug_dataset_version_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
) -> DrugUpdaterStatus:
    current_drug_dataset = await drug_dataset_version_crud.get_current_active()
    latest_drug_dataset = await drug_dataset_version_crud.get_latest()

    last_update_run_error = None
    last_update_run_datetime_utc = None
    update_running = False
    if latest_drug_dataset:
        last_update_run_datetime_utc = latest_drug_dataset.import_end_datetime_utc
        if latest_drug_dataset.import_error:
            last_update_run_error = latest_drug_dataset.import_error
        if latest_drug_dataset.import_status in ["queued", "running"]:
            update_running = True

    current_drug_data_ready_to_use = False
    if current_drug_dataset and current_drug_dataset.import_status == "done":
        current_drug_data_ready_to_use = True

    return DrugUpdaterStatus(
        update_available=False,  # Todo: Query the drug db module for available updates
        update_running=update_running,
        last_update_run_datetime_utc=last_update_run_datetime_utc,
        last_update_run_error=last_update_run_error,
        current_drug_data_version=current_drug_dataset.dataset_version
        if current_drug_dataset
        else None,
        current_drug_data_ready_to_use=current_drug_data_ready_to_use,
    )
