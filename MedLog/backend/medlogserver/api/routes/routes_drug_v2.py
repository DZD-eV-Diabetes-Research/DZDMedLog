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

import asyncio

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

from medlogserver.db.wido_gkv_arzneimittelindex import StammCRUD, StammUserCustomCRUD


from medlogserver.db.drug_data.drug import DrugCRUD

from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.model.drug_data.api_drug_model_factory import (
    drug_api_read_class_factory,
)

from medlogserver.model.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    DrugAttrFieldDefinitionAPIRead,
)
from medlogserver.db.drug_data.drug_lov_values import DrugAttrFieldLovItemCRUD
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
    DrugAttrFieldLovItemAPIRead,
)

DrugRead = drug_api_read_class_factory()
config = Config()

from medlogserver.log import get_logger

log = get_logger()


drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

fast_api_drug_router_v2: APIRouter = APIRouter(prefix="/v2")


# class StammQueryParams(QueryParamsGeneric[StammRead]):
#    defaults = {"limit": 100}


DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugRead)


#############
@fast_api_drug_router_v2.get(
    "/drug",
    response_model=PaginatedResponse[DrugRead],
    description=f"List all medicine/drugs from the system. {NEEDS_ADMIN_API_INFO}",
)
async def list_drugs(
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    pagination: QueryParamsInterface = Depends(DrugQueryParams),
    drug_crud: DrugCRUD = Depends(DrugCRUD.get_crud),
) -> PaginatedResponse[DrugRead]:
    result_items = await drug_crud.list(pagination=pagination)
    # return result_items
    return pagination(
        total_count=await drug_crud.count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )


drug_importer = drug_importer_class()
field_defs: List[DrugAttrFieldDefinition] = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_ref_attr_field_definitions()
)


@fast_api_drug_router_v2.get(
    "/drug/enum",
    response_model=List[DrugAttrFieldDefinitionAPIRead],
    description=f"List all enum fields for the current drug dataset",
)
async def list_enum_fields(
    user: User = Security(get_current_user),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> List[DrugAttrFieldDefinitionAPIRead]:
    return [f for f in field_defs if f.has_list_of_values]


@fast_api_drug_router_v2.get(
    "/drug/enum/{field_name}",
    response_model=DrugAttrFieldDefinitionAPIRead,
    description=f"Get enum field data for the certain field",
)
async def get_enum_field(
    field_name: str,
    user: User = Security(get_current_user),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> DrugAttrFieldDefinitionAPIRead:
    try:
        return next(f for f in field_defs if f.field_name == field_name)
    except StopIteration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug enum field with name '{field_name}' could not be found.",
        )


LovItemQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    DrugAttrFieldLovItemAPIRead, default_order_by_attr="sort_order", default_limit=100
)


@fast_api_drug_router_v2.get(
    "/drug/enum/{field_name}/val",
    response_model=PaginatedResponse[DrugAttrFieldLovItemAPIRead],
    description=f"List all enum fields for the current drug dataset",
)
async def get_enum_field_values(
    field_name: str,
    user: User = Security(get_current_user),
    pagination: QueryParamsInterface = Depends(LovItemQueryParams),
    drug_lov_item_crud: DrugAttrFieldLovItemCRUD = Depends(
        DrugAttrFieldLovItemCRUD.get_crud
    ),
) -> PaginatedResponse[DrugAttrFieldLovItemAPIRead]:
    result_items = await drug_lov_item_crud.list(
        field_name=field_name, pagination=pagination
    )
    total_count = await drug_lov_item_crud.count(field_name=field_name)
    return PaginatedResponse(
        total_count=total_count,
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )
