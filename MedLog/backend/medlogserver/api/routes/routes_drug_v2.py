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
from pydantic import BaseModel, Field, create_model
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


class DrugAttrFieldDefinitionContainer(BaseModel):
    attrs: List[DrugAttrFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'Free-form field'-attributes a drug can have."
    )
    ref_attrs: List[DrugAttrFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'selection-field' attributes (aka 'list of values'-fields, 'enum'-field or 'reference'-field) a drug can have."
    )


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
    drug_importer.get_attr_field_definitions()
)
field_ref_defs: List[
    DrugAttrFieldDefinition
] = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_ref_attr_field_definitions()
)


@fast_api_drug_router_v2.get(
    "/drug/field_def",
    response_model=DrugAttrFieldDefinitionContainer,
    description=f"List all field definitions for the current drug dataset",
)
async def list_field_definitions(
    user: User = Security(get_current_user),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> DrugAttrFieldDefinitionContainer:

    # we need to cast from DrugAttrFieldDefinition to DrugAttrFieldDefinitionAPIRead manually
    # this is because the DrugAttrFieldDefinition.type field can not be transated into a string value by fastapi/pydantic.
    # this is an ugly hack.
    # Todo: improve the code/datastructure of DrugAttrFieldDefinition and DrugAttrFieldDefinitionAPIRead to make this less cluttered
    result_container = DrugAttrFieldDefinitionContainer(attrs=[], ref_attrs=[])
    for field_def in field_ref_defs + field_defs:
        field_def_read_vals = {}
        for k, v in field_def.model_dump(exclude_unset=True).items():
            if k in DrugAttrFieldDefinitionAPIRead.model_fields.keys():
                if k == "type":
                    v = v.name
                field_def_read_vals[k] = v
        if field_def.has_list_of_values:
            result_container.ref_attrs.append(
                DrugAttrFieldDefinitionAPIRead(**field_def_read_vals)
            )
        else:
            result_container.attrs.append(
                DrugAttrFieldDefinitionAPIRead(**field_def_read_vals)
            )
    return result_container


@fast_api_drug_router_v2.get(
    "/drug/field_def/{field_name}",
    response_model=DrugAttrFieldDefinitionAPIRead,
    description=f"Get enum field data for the certain field",
)
async def get_field_definition(
    field_name: str,
    user: User = Security(get_current_user),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> DrugAttrFieldDefinitionAPIRead:
    try:
        field_def: DrugAttrFieldDefinition = next(
            f for f in field_ref_defs + field_defs if f.field_name == field_name
        )
    except StopIteration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug enum field with name '{field_name}' could not be found.",
        )
    # we need to cast from DrugAttrFieldDefinition to DrugAttrFieldDefinitionAPIRead manually
    # this is because the DrugAttrFieldDefinition.type field can not be transated into a string value by fastapi/pydantic.
    # this is an ugly hack.
    # Todo: improve the code/datastructure of DrugAttrFieldDefinition and DrugAttrFieldDefinitionAPIRead to make this less cluttered
    field_def_read_vals = {}
    for k, v in field_def.model_dump(exclude_unset=True).items():
        if k in DrugAttrFieldDefinitionAPIRead.model_fields.keys():
            if k == "type":
                v = v.name
            field_def_read_vals[k] = v
    return DrugAttrFieldDefinitionAPIRead(**field_def_read_vals)


LovItemQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    DrugAttrFieldLovItemAPIRead, default_order_by_attr="sort_order", default_limit=100
)


@fast_api_drug_router_v2.get(
    "/drug/field_def/{field_name}/refs",
    response_model=PaginatedResponse[DrugAttrFieldLovItemAPIRead],
    description=f"List possible values (List of values) for an enum field",
)
async def get_reference_field_values(
    field_name: str,
    search_term: str = Query(
        default=None,
        description="If a search term is provided the list will be filtered by this string",
    ),
    user: User = Security(get_current_user),
    pagination: QueryParamsInterface = Depends(LovItemQueryParams),
    drug_lov_item_crud: DrugAttrFieldLovItemCRUD = Depends(
        DrugAttrFieldLovItemCRUD.get_crud
    ),
) -> PaginatedResponse[DrugAttrFieldLovItemAPIRead]:
    if field_name not in [f.field_name for f in field_ref_defs]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drug enum field with name '{field_name}' could not be found.",
        )
    result_items = await drug_lov_item_crud.list(
        field_name=field_name, pagination=pagination, search_term=search_term
    )
    total_count = await drug_lov_item_crud.count(
        field_name=field_name, search_term=search_term
    )
    return PaginatedResponse(
        total_count=total_count,
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )


drug_search_filter_ref_fields = {}
for f in field_ref_defs:
    drug_search_filter_ref_fields["filter_" + f.field_name] = (
        int if f.type.name == "INT" else str,
        None,
    )
drug_search_query_model = create_model("Query", **drug_search_filter_ref_fields)


@fast_api_drug_router_v2.get(
    "/drug/search",
    response_model=PaginatedResponse[DrugRead],
    description=f"List all medicine/drugs from the system. {NEEDS_ADMIN_API_INFO}",
)
async def search_drugs(
    search_term: Annotated[
        str,
        Query(
            description="A search term. Can be multiple words or a single one. One word must be at least 3 chars or contained in a longer quoted string (e.g. `'Salofalk 1 g'` instead of `Salofalk 1 g`)",
            min_length=3,
        ),
    ],
    filter_params: drug_search_query_model = Depends(),
    user: User = Security(get_current_user),
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