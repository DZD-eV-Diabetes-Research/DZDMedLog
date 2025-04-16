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


from medlogserver.utils import get_app_version, get_version_git_branch_name

from medlogserver.model.app_version import AppVersion
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_config_router: APIRouter = APIRouter()


@fast_api_config_router.get(
    "/config/version",
    response_model=AppVersion,
    description=f"Get the basic health state of the system.",
)
async def get_version() -> AppVersion:
    return AppVersion(version=get_app_version(), branch=get_version_git_branch_name())
