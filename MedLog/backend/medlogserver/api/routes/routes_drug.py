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
from medlogserver.db.wido_gkv_arzneimittelindex.drug_search._base import (
    MedLogSearchEngineResult,
)
from medlogserver.model.wido_gkv_arzneimittelindex import (
    Normpackungsgroessen,
    Darreichungsform,
    Applikationsform,
    Generikakennung,
    ApoPflicht,
    Preisart,
    Hersteller,
)
from medlogserver.db.wido_gkv_arzneimittelindex import (
    NormpackungsgroessenCRUD,
    DarreichungsformCRUD,
    ApplikationsformCRUD,
    GenerikakennungCRUD,
    ApoPflichtCRUD,
    PreisartCRUD,
    HerstellerCRUD,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_drug_router: APIRouter = APIRouter()


# class StammQueryParams(QueryParamsGeneric[StammRead]):
#    defaults = {"limit": 100}


StammQueryParams: Type[QueryParamsInterface] = create_query_params_class(StammRead)


#############
@fast_api_drug_router.get(
    "/drug",
    response_model=PaginatedResponse[StammRead],
    description=f"List all medicine/drugs from the system. {NEEDS_ADMIN_API_INFO}",
)
async def list_drugs(
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    pagination: QueryParamsInterface = Depends(StammQueryParams),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> PaginatedResponse[StammRead]:
    result_items = await drug_stamm_crud.list(pagination=pagination)
    # return result_items
    return pagination(
        total_count=await drug_stamm_crud.count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )


@fast_api_drug_router.get(
    "/drug/by-pzn/{pzn}",
    response_model=StammRead,
    description=f"Get a drugs data by its PZN",
)
async def get_drug(
    pzn: str,
    user: User = Security(get_current_user),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> StammRead:
    return await drug_stamm_crud.get(
        pzn,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drug found with Pharmazentralnummer '{pzn}'",
        ),
    )


MedLogSearchEngineResultQueryParams: Type[QueryParamsInterface] = (
    create_query_params_class(
        MedLogSearchEngineResult, non_sortable_attributes=["pzn", "item"]
    )
)


@fast_api_drug_router.get(
    "/drug/search",
    response_model=PaginatedResponse[MedLogSearchEngineResult],
    description=f"Search medicine/drugs from the system",
)
async def search_drugs(
    search_term: Annotated[
        str,
        Query(
            description="A search term. Can be multiple words or a single one. One word must be at least 3 chars or contained in a longer quoted string (e.g. `'Salofalk 1 g'` instead of `Salofalk 1 g`)",
            min_length=3,
        ),
    ],
    pzn_contains: str = None,
    filter_packgroesse: str = None,
    filter_darrform: str = None,
    filter_appform: str = None,
    filter_normpackungsgroeße_zuzahlstufe: str = None,
    filter_atc_level2: str = None,
    filter_generikakenn: str = None,
    filter_apopflicht: int = None,
    filter_preisart_neu: str = None,
    only_current_medications: bool = True,
    pagination: QueryParamsInterface = Depends(MedLogSearchEngineResultQueryParams),
    drug_search: DrugSearch = Depends(get_drug_search),
    user: User = Security(get_current_user),
) -> PaginatedResponse[MedLogSearchEngineResult]:
    try:
        return await drug_search.search(
            search_term=search_term,
            pzn_contains=pzn_contains,
            filter_packgroesse=filter_packgroesse,
            filter_darrform=filter_darrform,
            filter_appform=filter_appform,
            filter_normpackungsgroeße_zuzahlstufe=filter_normpackungsgroeße_zuzahlstufe,
            filter_atc_level2=filter_atc_level2,
            filter_generikakenn=filter_generikakenn,
            filter_apopflicht=filter_apopflicht,
            filter_preisart_neu=filter_preisart_neu,
            only_current_medications=only_current_medications,
            pagination=pagination,
        )
    except SearchEngineNotReadyException as err:
        # the search engine is still warming up. the user has to wait a bit
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=repr(repr(err))
        )

    return await drug_search.total_drug_count()
    return PaginatedResponse(
        total_count=await drug_search.total_drug_count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )
    # return await drug_stamm_crud.list()


NormpackungsgroessenQueryParams: Type = create_query_params_class(Normpackungsgroessen)


@fast_api_drug_router.get(
    "/drug/enum/normpackungsgroessen",
    response_model=PaginatedResponse[Normpackungsgroessen],
    description=f"list normpackungsgroessen",
)
async def list_packgroesse(
    user: User = Security(get_current_user),
    normp_crud: NormpackungsgroessenCRUD = Depends(NormpackungsgroessenCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(NormpackungsgroessenQueryParams),
) -> PaginatedResponse[Normpackungsgroessen]:
    res = await normp_crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await normp_crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


DarreichungsformQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Darreichungsform
)


@fast_api_drug_router.get(
    "/drug/enum/darrform",
    response_model=PaginatedResponse[Darreichungsform],
    description=f"list ...",
)
async def list_darreichungsforms(
    user: User = Security(get_current_user),
    crud: DarreichungsformCRUD = Depends(DarreichungsformCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(DarreichungsformQueryParams),
) -> PaginatedResponse[Darreichungsform]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


ApplikationsformQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Applikationsform
)


@fast_api_drug_router.get(
    "/drug/enum/appform",
    response_model=PaginatedResponse[Applikationsform],
    description=f"list Applikationsform",
)
async def list_applikationsforms(
    user: User = Security(get_current_user),
    crud: ApplikationsformCRUD = Depends(ApplikationsformCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(ApplikationsformQueryParams),
) -> PaginatedResponse[Applikationsform]:
    res = await crud.list(pagination=pagination)
    # print("API RES", res)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.get(
    "/drug/enum/appform/{key}",
    response_model=Applikationsform,
    description=f"list Applikationsform",
)
async def get_applikationsform(
    key: str,
    user: User = Security(get_current_user),
    crud: ApplikationsformCRUD = Depends(ApplikationsformCRUD.get_crud),
) -> Applikationsform:
    return await crud.get(key=key)


GenerikakennungQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Generikakennung
)


@fast_api_drug_router.get(
    "/drug/enum/generikakenn",
    response_model=PaginatedResponse[Generikakennung],
    description=f"list Generikakennung",
)
async def list_generikakenns(
    user: User = Security(get_current_user),
    crud: GenerikakennungCRUD = Depends(GenerikakennungCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(GenerikakennungQueryParams),
) -> PaginatedResponse[Generikakennung]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


ApoPflichtQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    ApoPflicht
)


@fast_api_drug_router.get(
    "/drug/enum/apopflicht",
    response_model=PaginatedResponse[ApoPflicht],
    description=f"list ApoPflicht",
)
async def list_apopflicht(
    user: User = Security(get_current_user),
    crud: ApoPflichtCRUD = Depends(ApoPflichtCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(ApoPflichtQueryParams),
) -> PaginatedResponse[ApoPflicht]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


PreisartQueryParams: Type[QueryParamsInterface] = create_query_params_class(Preisart)


@fast_api_drug_router.get(
    "/drug/enum/preisart",
    response_model=PaginatedResponse[Preisart],
    description=f"list Preisart",
)
async def list_preisart(
    user: User = Security(get_current_user),
    crud: PreisartCRUD = Depends(PreisartCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(PreisartQueryParams),
) -> PaginatedResponse[Preisart]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


HerstellerQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Hersteller
)


@fast_api_drug_router.get(
    "/drug/enum/hersteller",
    response_model=PaginatedResponse[Hersteller],
    description=f"list or search herstellers",
)
async def list_hersteller(
    search_term: str = None,
    user: User = Security(get_current_user),
    crud: HerstellerCRUD = Depends(HerstellerCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(HerstellerQueryParams),
) -> PaginatedResponse[Preisart]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.post(
    "/drug/user-custom",
    response_model=StammUserCustomRead,
    description=f"Create a custom drug which one could not be found in the Arzneimittelindex.",
)
async def create_user_custom_drug(
    drug_create: StammUserCustomCreateAPI,
    user: User = Security(get_current_user),
    crud: StammUserCustomCRUD = Depends(StammUserCustomCRUD.get_crud),
) -> StammUserCustomRead:
    drug = StammUserCustom(created_by_user=user.id, **drug_create.model_dump())
    return await crud.create(drug)


@fast_api_drug_router.get(
    "/drug/user-custom/my",
    response_model=PaginatedResponse[StammUserCustomRead],
    description=f"List my own custom drugs.",
)
async def list_users_custom_drugs(
    user: User = Security(get_current_user),
    crud: StammUserCustomCRUD = Depends(StammUserCustomCRUD.get_crud),
) -> PaginatedResponse[StammUserCustomRead]:
    return await crud.list(filter_user_id=user.id)


@fast_api_drug_router.get(
    "/drug/user-custom/{drug_custom_id}",
    response_model=StammUserCustomRead,
    description=f"List my own custom drugs.",
)
async def get_user_custom_drugs(
    drug_custom_id: uuid.UUID,
    user: User = Security(get_current_user),
    crud: StammUserCustomCRUD = Depends(StammUserCustomCRUD.get_crud),
) -> StammUserCustomRead:
    return await crud.get(id=drug_custom_id)
