from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn, Type
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
)

from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.db.user import User

from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.api.routes.routes_auth import NEEDS_ADMIN_API_INFO
from medlogserver.api.study_access import (
    get_current_user,
)


from medlogserver.config import Config
from medlogserver.model.wido_gkv_arzneimittelindex import (
    StammRead,
    StammUserCustomRead,
    StammRoot,
    StammUserCustomCreateAPI,
    StammUserCustom,
)
from medlogserver.db.wido_gkv_arzneimittelindex import StammCRUD, StammUserCustomCRUD


from medlogserver.db.wido_gkv_arzneimittelindex.drug_search import (
    DrugSearch,
    get_drug_search,
    SearchEngineNotConfiguredException,
    SearchEngineNotReadyException,
)
from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.model.drug_data.api_model_factory import (
    drug_api_read_class_factory,
)

DrugRead = drug_api_read_class_factory()
config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_drug_router_v2: APIRouter = APIRouter(prefix="/v2")


# class StammQueryParams(QueryParamsGeneric[StammRead]):
#    defaults = {"limit": 100}


StammQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugRead)


#############
@fast_api_drug_router_v2.get(
    "/drug",
    response_model=PaginatedResponse[DrugRead],
    description=f"List all medicine/drugs from the system. {NEEDS_ADMIN_API_INFO}",
)
async def list_drugs(
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    pagination: QueryParamsInterface = Depends(StammQueryParams),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> PaginatedResponse[DrugRead]:
    result_items = await drug_stamm_crud.list(pagination=pagination)
    # return result_items
    return pagination(
        total_count=await drug_stamm_crud.count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )
