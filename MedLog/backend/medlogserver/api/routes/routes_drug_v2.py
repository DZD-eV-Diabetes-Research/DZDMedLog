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
)
from itertools import chain
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


from medlogserver.db.drug_data.drug import DrugCRUD

from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugAPIRead,
    drug_to_drugAPI_obj,
)
from medlogserver.model.drug_data.drug import DrugCustomCreate
from medlogserver.db.drug_data.drug import (
    DrugWithCodeAllreadyExists,
    CustomDrugAttrNotValid,
)
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    DrugAttrFieldDefinitionAPIReadBase,
    DrugAttrFieldDefinitionAPIRead,
    DrugAttrRefFieldDefinitionAPIRead,
    DrugAttrMultiRefFieldDefinitionAPIRead,
    DrugAttrMultiFieldDefinitionAPIRead,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.db.drug_data.drug_lov_values import DrugAttrFieldLovItemCRUD
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
    DrugAttrFieldLovItemAPIRead,
)
from medlogserver.db.drug_data.drug_code_system import DrugCodeSystemCRUD
from medlogserver.db.drug_data.drug_dataset_version import DrugDataSetVersionCRUD
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion


config = Config()

from medlogserver.log import get_logger

log = get_logger()


drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

fast_api_drug_router_v2: APIRouter = APIRouter(prefix="/v2")

drug_importer = drug_importer_class()
"""
# all fields a drug based current drug importer module can have
drug_field_attr_defs: List[
    DrugAttrFieldDefinition
] = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_attr_field_definitions()
)

drug_field_attr_multi_defs: List[
    DrugAttrFieldDefinition
] = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_attr_multi_field_definitions()
)

# all reference fields (select values) a drug based current drug importer module can have
drug_field_attr_ref_defs: List[
    DrugAttrFieldDefinition
] = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_attr_ref_field_definitions()
)

drug_field_attr_multi_ref_defs = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_attr_multi_ref_field_definitions()
)
"""
drug_field_definitions = asyncio.get_event_loop().run_until_complete(
    drug_importer.get_all_attr_field_definitions()
)
drug_field_api_read_types = {
    "attrs": DrugAttrFieldDefinitionAPIRead,
    "attrs_ref": DrugAttrRefFieldDefinitionAPIRead,
    "attrs_multi": DrugAttrMultiFieldDefinitionAPIRead,
    "attrs_multi_ref": DrugAttrMultiRefFieldDefinitionAPIRead,
}

# all searchable fields a drug based in the current drug import can have
drug_search_filter_ref_fields = {}
for f in drug_field_definitions["attrs_ref"]:
    drug_search_filter_ref_fields["filter_" + f.field_name] = (
        Optional[int if f.type.name == "INT" else str],
        None,
    )


drug_search_query_model: type[BaseModel] = create_model(
    "Query", **drug_search_filter_ref_fields
)


from medlogserver.db.drug_data.drug_search._base import MedLogSearchEngineResult
from medlogserver.db.drug_data.drug_search.search_interface import (
    get_drug_search,
    DrugSearch,
)


DrugQueryParams: Type[QueryParamsInterface] = create_query_params_class(DrugAPIRead)


class DrugAttrFieldDefinitionContainer(BaseModel):
    attrs: List[DrugAttrFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'Free-form field'-attributes a drug can have."
    )
    attrs_multi: List[DrugAttrMultiFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'Free-form field'-attributes a drug can have."
    )
    attrs_ref: List[DrugAttrRefFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'selection-field' attributes (aka 'list of values'-fields, 'enum'-field or 'reference'-field) a drug can have."
    )
    attrs_multi_ref: List[DrugAttrMultiRefFieldDefinitionAPIRead] = Field(
        description="Metadata for all 'selection-field' attributes (aka 'list of values'-fields, 'enum'-field or 'reference'-field) a drug can have."
    )


@fast_api_drug_router_v2.get(
    "/drug/search",
    response_model=PaginatedResponse[MedLogSearchEngineResult],
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
    market_accessable: Annotated[
        Optional[bool],
        Query(
            description="'null': List all drugs, 'true': List only drug that are currently available on the market. 'false': List only drugs that are not market accessable anymore.",
        ),
    ] = None,
    filter_params: drug_search_query_model = Depends(),
    user: User = Security(get_current_user),
    drug_search: DrugSearch = Depends(get_drug_search),
    pagination: QueryParamsInterface = Depends(DrugQueryParams),
) -> PaginatedResponse[MedLogSearchEngineResult]:
    search_results = await drug_search.search(
        search_term=search_term,
        market_accessable=market_accessable,
        pagination=pagination,
        **filter_params.model_dump(),
    )
    return search_results


@fast_api_drug_router_v2.get(
    "/drug/id/{drug_id}",
    response_model=DrugAPIRead,
    description=f"Get a certain drug by its id",
)
async def get_drug(
    drug_id: uuid.UUID,
    user: User = Security(get_current_user),
    drug_crud: DrugCRUD = Depends(DrugCRUD.get_crud),
) -> DrugAPIRead:
    drug_result = await drug_crud.get(
        id_=drug_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drug with ID '{drug_id}' can be found",
        ),
    )
    return await drug_to_drugAPI_obj(drug_result)


#############
""" 
#this endpoint throws out all drug in the system. only for debuging. 
#will propably crash with a fully loaded drug dataset and also makes it possible to export the drug dataset which is nothing we want

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
    result_items = await drug_crud.list(include_relations=True, pagination=pagination)
    # return result_items
    result_items_as_api_read_objs = [await drug_to_drugAPI_obj(i) for i in result_items]
    return PaginatedResponse(
        total_count=await drug_crud.count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items_as_api_read_objs,
    )
"""


@fast_api_drug_router_v2.get(
    "/drug/field_def",
    response_model=DrugAttrFieldDefinitionContainer,
    description=f"List all field definitions for the current drug dataset",
)
async def list_field_definitions(
    user: User = Security(get_current_user),
) -> DrugAttrFieldDefinitionContainer:
    # we need to cast from DrugAttrFieldDefinition to DrugAttrFieldDefinitionAPIRead manually
    # this is because the DrugAttrFieldDefinition.type field can not be transated into a string value by fastapi/pydantic.
    # this is an ugly hack.
    # Todo: improve the code/datastructure of DrugAttrFieldDefinition and DrugAttrFieldDefinitionAPIRead to make this less cluttered
    result_container = DrugAttrFieldDefinitionContainer(
        attrs=[], attrs_ref=[], attrs_multi_ref=[], attrs_multi=[]
    )

    for drug_attr_type_name, drug_attr_defs in drug_field_definitions.items():

        for field_def in drug_attr_defs:
            field_def_read_vals = {}
            for k, v in field_def.model_dump(exclude_unset=True).items():
                if k in DrugAttrFieldDefinitionAPIRead.model_fields.keys():
                    if k == "type":
                        # from the "type"-enum attribute we only want the name (INT,STR,FLOAT,...), not the value (casting function)
                        v = v.name
                    field_def_read_vals[k] = v

            if drug_attr_type_name == "attrs":
                result_container.attrs.append(
                    DrugAttrFieldDefinitionAPIRead(**field_def_read_vals)
                )
            elif drug_attr_type_name == "attrs_ref":
                result_container.attrs_ref.append(
                    DrugAttrRefFieldDefinitionAPIRead(**field_def_read_vals)
                )
            elif drug_attr_type_name == "attrs_multi":
                result_container.attrs_multi.append(
                    DrugAttrMultiFieldDefinitionAPIRead(**field_def_read_vals)
                )
            elif drug_attr_type_name == "attrs_multi_ref":
                result_container.attrs_multi_ref.append(
                    DrugAttrMultiRefFieldDefinitionAPIRead(**field_def_read_vals)
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
) -> DrugAttrFieldDefinitionAPIRead:
    try:
        field_def: DrugAttrFieldDefinition = next(
            f
            for f in list(chain.from_iterable(drug_field_definitions.values()))
            if f.field_name == field_name
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
    description=f"List possible values, display values, sort_oder of a LOV (List of values) for a reference field.",
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
    if field_name not in [
        f.field_name
        for f in drug_field_definitions["attrs_ref"]
        + drug_field_definitions["attrs_multi_ref"]
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug enum field with name '{field_name}' could not be found.",
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


@fast_api_drug_router_v2.get(
    "/drug/field_def/{field_name}/refs/{ref_val}",
    response_model=DrugAttrFieldLovItemAPIRead,
    description=f"get a certain values, display values, sort_oder of a LOV (List of values) for a reference field.",
)
async def get_reference_field_value(
    field_name: str,
    ref_val: str,
    user: User = Security(get_current_user),
    drug_lov_item_crud: DrugAttrFieldLovItemCRUD = Depends(
        DrugAttrFieldLovItemCRUD.get_crud
    ),
) -> DrugAttrFieldLovItemAPIRead:
    if field_name not in [
        f.field_name
        for f in drug_field_definitions["attrs_ref"]
        + drug_field_definitions["attrs_multi_ref"]
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug enum field with name '{field_name}' could not be found.",
        )
    return await drug_lov_item_crud.get(
        field_name=field_name,
        value=ref_val,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drug enum field with name '{field_name}' and value {ref_val} could not be found.",
        ),
    )


@fast_api_drug_router_v2.get(
    "/drug/code_def",
    response_model=List[DrugCodeSystem],
    description=f"List all drug coding system used in the current drug dataset.",
)
async def list_drug_code_systems(
    user: User = Security(get_current_user),
    drug_code_sys_crud: DrugCodeSystemCRUD = Depends(DrugCodeSystemCRUD.get_crud),
) -> List[DrugCodeSystem]:
    return await drug_code_sys_crud.list()


@fast_api_drug_router_v2.get(
    "/drug/code_def/{code_id}",
    response_model=DrugCodeSystem,
    description=f"List detail if a specific drug code system",
)
async def get_drug_code_details(
    code_id: str,
    user: User = Security(get_current_user),
    drug_code_sys_crud: DrugCodeSystemCRUD = Depends(DrugCodeSystemCRUD.get_crud),
) -> DrugAttrFieldLovItemAPIRead:
    return await drug_code_sys_crud.get(code_id)


@fast_api_drug_router_v2.post(
    "/drug/custom",
    response_model=DrugAPIRead,
    description=f"Add a custom drug to the drug database. Should be used as a last resort if the user can not find a specific drug in the search.",
)
async def create_custom_drug(
    custom_drug: DrugCustomCreate,
    user: User = Security(get_current_user),
    drug_dataset_crud: DrugDataSetVersionCRUD = Depends(
        DrugDataSetVersionCRUD.get_crud
    ),
    drug_crud: DrugCRUD = Depends(DrugCRUD.get_crud),
) -> DrugAPIRead:
    custom_drug_dataset = await drug_dataset_crud.get_custom()
    try:
        new_custom_drug = await drug_crud.create_custom(
            drug_create=custom_drug, custom_drug_dataset=custom_drug_dataset
        )
    except DrugWithCodeAllreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CustomDrugAttrNotValid as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    return await drug_to_drugAPI_obj(new_custom_drug)
