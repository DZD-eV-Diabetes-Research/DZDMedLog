from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn

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

from medlogserver.db.user.crud import User


from medlogserver.api.auth.base import (
    user_is_admin,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
)
from medlogserver.api.routes_app.security import (
    get_current_user,
)


from medlogserver.config import Config
from medlogserver.db.wido_gkv_arzneimittelindex.model import StammRead
from medlogserver.db.wido_gkv_arzneimittelindex.crud import StammCRUD


from medlogserver.db.wido_gkv_arzneimittelindex.drug_search import (
    DrugSearch,
    get_drug_search,
    SearchEngineNotConfiguredException,
    SearchEngineNotReadyException,
)
from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import pagination_query, PageParams, PaginatedResponse
from medlogserver.db.wido_gkv_arzneimittelindex.drug_search._base import (
    MedLogSearchEngineResult,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model import (
    Normpackungsgroessen,
    Darreichungsform,
    Applikationsform,
    Generikakennung,
    ApoPflicht,
    Preisart,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud import (
    NormpackungsgroessenCRUD,
    DarreichungsformCRUD,
    ApplikationsformCRUD,
    GenerikakennungCRUD,
    ApoPflichtCRUD,
    PreisartCRUD,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_drug_router: APIRouter = APIRouter()


#############
@fast_api_drug_router.get(
    "/drug",
    response_model=PaginatedResponse[StammRead],
    description=f"List all medicine/drugs from the system. {NEEDS_ADMIN_API_INFO}",
)
async def list_drugs(
    user: User = Security(get_current_user),
    is_admin: bool = Security(user_is_admin),
    pagination: PageParams = Depends(pagination_query),
    drug_stamm_crud: StammCRUD = Depends(StammCRUD.get_crud),
) -> PaginatedResponse[StammRead]:
    result_items = await drug_stamm_crud.list(pagination=pagination)
    # return result_items
    return PaginatedResponse(
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
        pzn=pzn,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drug found with Pharmazentralnummer '{pzn}'",
        ),
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
    pagination: PageParams = Depends(pagination_query),
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
        # the search engine is still warming up. the user hat so wait a bit
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


@fast_api_drug_router.get(
    "/drug/enum/normpackungsgroessen",
    response_model=PaginatedResponse[Normpackungsgroessen],
    description=f"list normpackungsgroessen",
)
async def list_packgroesse(
    user: User = Security(get_current_user),
    normp_crud: NormpackungsgroessenCRUD = Depends(NormpackungsgroessenCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Normpackungsgroessen]:
    res = await normp_crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await normp_crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.get(
    "/drug/enum/darrform",
    response_model=PaginatedResponse[Darreichungsform],
    description=f"list ...",
)
async def list_darreichungsforms(
    user: User = Security(get_current_user),
    crud: DarreichungsformCRUD = Depends(DarreichungsformCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Darreichungsform]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.get(
    "/drug/enum/appform",
    response_model=PaginatedResponse[Applikationsform],
    description=f"list Applikationsform",
)
async def list_applikationsforms(
    user: User = Security(get_current_user),
    crud: ApplikationsformCRUD = Depends(ApplikationsformCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Applikationsform]:
    res = await crud.list(pagination=pagination)
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
async def list_applikationsforms(
    key: str,
    user: User = Security(get_current_user),
    crud: ApplikationsformCRUD = Depends(ApplikationsformCRUD.get_crud),
) -> Applikationsform:
    return await crud.get(key=key)


@fast_api_drug_router.get(
    "/drug/enum/generikakenn",
    response_model=PaginatedResponse[Generikakennung],
    description=f"list Generikakennung",
)
async def list_generikakenns(
    user: User = Security(get_current_user),
    crud: GenerikakennungCRUD = Depends(GenerikakennungCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Generikakennung]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.get(
    "/drug/enum/apopflicht",
    response_model=PaginatedResponse[ApoPflicht],
    description=f"list ApoPflicht",
)
async def list_apopflicht(
    user: User = Security(get_current_user),
    crud: ApoPflichtCRUD = Depends(ApoPflichtCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[ApoPflicht]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


@fast_api_drug_router.get(
    "/drug/enum/preisart",
    response_model=PaginatedResponse[Preisart],
    description=f"list Preisart",
)
async def list_apopflicht(
    user: User = Security(get_current_user),
    crud: PreisartCRUD = Depends(PreisartCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Preisart]:
    res = await crud.list(pagination=pagination)
    return PaginatedResponse(
        total_count=await crud.count(),
        offset=pagination.offset,
        count=len(res),
        items=res,
    )


"""
############
@fast_api_drug_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands last completed interview.",
)
async def list_all_intakes_of_last_uncompleted_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    last_uncompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if last_uncompleted_interview:
        return await intake_crud.list(
            filter_interview_id=last_uncompleted_interview.id
        )
    else:
        return []


############
@fast_api_drug_router.get(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of interview.",
)
async def list_all_intakes_of_interview(
    interview_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:

    return await intake_crud.list(
        filter_interview_id=interview_id, filter_study_id=study_access.study.id
    )


############
@fast_api_drug_router.get(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description=f"Get a certain intake record by it id",
)
async def get_intake(
    intake_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> Intake:
    return await intake_crud.get(
        intake_id=intake_id,
        study_id=study_access.study.id,
        raise_exception_if_none=HTTPException(status_code=status.HTTP_404_NOT_FOUND),
    )


############
@fast_api_drug_router.post(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"Create intake record in certain interview. user must have at least 'interviewer'-permissions on study.",
)
async def create_intake(
    interview_id: str,
    intake: IntakeCreate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of the study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    intake.interview_id == interview_id
    return await intake_crud.create(intake)


############
@fast_api_drug_router.patch(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=List[Intake],
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def update_intake(
    interview_id: str,
    intake_id: str,
    intake: IntakeUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    intake.interview_id == interview_id
    return await intake_crud.update(intake_id, intake)


############
@fast_api_drug_router.delete(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=List[Intake],
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def delete_intake(
    interview_id: str,
    intake_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    log.warning("ToDo: The med record are not deleted yet")
    return await intake_crud.delete(intake_id)
"""
