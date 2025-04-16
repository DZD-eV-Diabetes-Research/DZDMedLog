from typing import Annotated, Sequence, List, Type
from datetime import datetime, timedelta, timezone


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


from medlogserver.config import Config
from medlogserver.db.user import UserCRUD
from medlogserver.model.healthcheck import HealthCheck, HealthCheckReport
from medlogserver.db.healthcheck import HealthcheckRead
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_healthcheck_router: APIRouter = APIRouter()


@fast_api_healthcheck_router.get(
    "/config/version",
    response_model=HealthCheck,
    description=f"Get the basic health state of the system.",
)
async def get_version(
    health_read: HealthcheckRead = Depends(HealthcheckRead.get_crud),
) -> HealthCheck:
    return await health_read.get()


@fast_api_healthcheck_router.get(
    "/health/report",
    response_model=HealthCheckReport,
    description=f"Get a more detailed health report of the system.",
)
async def get_health_report(
    user: UserCRUD = Security(get_current_user),
    health_read: HealthcheckRead = Depends(HealthcheckRead.get_crud),
) -> HealthCheckReport:
    return await health_read.get_report()


async def get_health_report(
    user: UserCRUD = Security(get_current_user),
    health_read: HealthcheckRead = Depends(HealthcheckRead.get_crud),
) -> HealthCheckReport:
    return await health_read.get_report()
