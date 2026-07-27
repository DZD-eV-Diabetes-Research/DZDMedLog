from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, Type, Optional

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
import uuid
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.api.paginator import (
    QueryParamsInterface,
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.db.user import (
    User,
)
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.api.routes.routes_auth import (
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)

from medlogserver.model.study import (
    Study,
    StudyUpdate,
    StudyCreate,
    StudyCreateAPI,
    ProbandExternalIdNormalization,
)
from medlogserver.db.study import StudyCRUD
from medlogserver.db.interview import InterviewCRUD
from medlogserver.model.study_permission import StudyPermisson
from medlogserver.db.study_permission import StudyPermissonCRUD
from medlogserver.api.study_access import (
    user_has_studies_access_map,
    UserStudyAccessCollection,
    UserStudyAccess,
    user_has_study_access,
)
from medlogserver.model._base_model import MedLogBaseModel
from medlogserver.utils import handle_integrity_error
from medlogserver.api.proband_id import (
    assert_valid_proband_id_pattern,
    check_proband_id,
    core_check_proband_id,
    ProbandIdValidationResult,
    ProbandIdPatternTestResult,
)

from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_study_router: APIRouter = APIRouter()

StudyQueryParams: Type[QueryParamsInterface] = create_query_params_class(Study)


@fast_api_study_router.get(
    "/study",
    response_model=PaginatedResponse[Study],
    description=f"List all studies the user has access too.",
)
async def list_studies(
    show_deactived: bool = Query(False),
    current_user: User = Security(get_current_user),
    study_permissions_helper: UserStudyAccessCollection = Security(
        user_has_studies_access_map
    ),
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(StudyQueryParams),
) -> PaginatedResponse[Study]:

    # ToDo: This is a pretty cost intensive endpoint/query. Would be a good candiate for some kind of cache. UPDATE: now all logic is in Security(user_has_study_access_map) fix/cache that

    # Thought (Tim): the pagination is everything but scalable in this Endpoint, because we fetch all studies, check them for permissions and paginate that result.
    # better would be a pagination on database level.
    # But we can assume that there will never be an MedLog instance that will host more than a couple of studies.
    # so everything is fine...
    all_studies = await study_crud.list(show_deactivated=show_deactived)
    allowed_studies: List[Study] = []
    if current_user.is_admin or current_user.is_usermanager:
        allowed_studies = all_studies
    else:
        for study in all_studies:
            if study_permissions_helper.user_has_access_to(study_id=study.id):
                allowed_studies.append(study)
    allowed_studies = pagination.order(allowed_studies)
    pageinated_allowed_studies = allowed_studies[pagination.offset : pagination.limit]
    return PaginatedResponse[Study](
        total_count=len(allowed_studies),
        offset=pagination.offset,
        count=len(pageinated_allowed_studies),
        items=pageinated_allowed_studies,
    )


@fast_api_study_router.post(
    "/study",
    response_model=Study,
    description=f"Create a new study. {NEEDS_ADMIN_API_INFO}",
)
async def create_study(
    study: StudyCreateAPI,
    current_user_is_admin: User = Security(user_is_admin),
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
) -> Study:
    # Reject a broken proband-ID regex up front so it can never be stored and later
    # break interview creation.
    assert_valid_proband_id_pattern(study.proband_external_id_pattern)
    study_create = StudyCreate(**study.model_dump(exclude_unset=True))
    return await study_crud.create(
        study_create,
        raise_custom_exception_if_exists=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Study with name '{study.display_name}' allready exists",
        ),
    )


@fast_api_study_router.patch(
    "/study/{study_id}",
    response_model=Study,
    description=f"Update existing study",
)
async def update_study(
    study_id: Annotated[uuid.UUID, Path()],
    study: Annotated[
        StudyUpdate, Body(description="The study object with updated data")
    ],
    confirm_normalization_change: Annotated[
        bool,
        Query(
            description=(
                "Must be set to true to change 'proband_external_id_normalization' on a "
                "study that already has interviews. Changing the normalization re-folds how "
                "proband IDs are matched, which can silently merge or split existing probands "
                "in lookups. Without this flag such a change is rejected with 409."
            )
        ),
    ] = False,
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
    study_permission_crud: StudyPermissonCRUD = Depends(StudyPermissonCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
    study_access: UserStudyAccess = Security(user_has_study_access),
    current_user: User = Security(get_current_user),
) -> Study:
    if not study_access.user_is_study_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not allowed to update this study",
        )
    assert_valid_proband_id_pattern(study.proband_external_id_pattern)

    # Guard (issue #318, item 5): changing the normalization rule on a study that already
    # has interviews re-folds how proband IDs are matched, which can silently merge two
    # distinct probands (e.g. under uppercase) or split one apart. Refuse such a change
    # unless the admin explicitly confirms it and report how many interviews are affected.
    if (
        "proband_external_id_normalization" in study.model_fields_set
        and study.proband_external_id_normalization
        != study_access.study.proband_external_id_normalization
        and not confirm_normalization_change
    ):
        existing_interviews = await interview_crud.list(filter_study_id=study_id)
        if len(existing_interviews) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": (
                        "Changing 'proband_external_id_normalization' on a study that "
                        "already has interviews can silently merge or split probands in "
                        "lookups. Re-submit with query parameter "
                        "'confirm_normalization_change=true' to proceed."
                    ),
                    "affected_interview_count": len(existing_interviews),
                    "current_normalization": study_access.study.proband_external_id_normalization.value,
                    "requested_normalization": study.proband_external_id_normalization.value,
                },
            )

    try:
        return await study_crud.update(id_=study_id, update_obj=study)
    except Exception as e:
        handle_integrity_error(e)


@fast_api_study_router.post(
    "/study/{study_id}/proband-external-id/validate",
    response_model=ProbandIdValidationResult,
    description=(
        "Validate a proband external ID against this study's configured pattern and "
        "normalization, without creating anything. Backs the frontend pre-submit check and the "
        "study-configuration test field. The backend stays authoritative on interview creation. "
        "Returns the normalized value and, if invalid, the study's human-readable error text."
    ),
)
async def validate_proband_external_id(
    proband_external_id: Annotated[str, Body(embed=True)],
    study_access: UserStudyAccess = Security(user_has_study_access),
) -> ProbandIdValidationResult:
    valid, normalized, error_text = check_proband_id(
        study_access.study, proband_external_id
    )
    return ProbandIdValidationResult(
        valid=valid,
        normalized_proband_external_id=normalized,
        error_text=error_text,
        proband_external_id_example=study_access.study.proband_external_id_example,
    )


class ProbandIdPatternTestRequest(MedLogBaseModel):
    """Body of the stateless 'test this pattern' endpoint."""

    pattern: Optional[str] = None
    normalization: ProbandExternalIdNormalization = (
        ProbandExternalIdNormalization.NONE
    )
    sample: str


@fast_api_study_router.post(
    "/proband-external-id/validate-pattern",
    response_model=ProbandIdPatternTestResult,
    description=(
        "Stateless helper for the study-configuration UI: validate a 'sample' proband ID "
        "against an *unsaved* 'pattern' + 'normalization', so a live test field can be "
        "offered before the study is saved. Touches no database. Returns whether the sample "
        "is valid, the normalized sample actually tested, an error text, and "
        "'pattern_compiles' (false when the entered regex does not compile). "
        f"Requires an authenticated user (intended for study administrators)."
    ),
)
async def validate_proband_external_id_pattern(
    body: Annotated[ProbandIdPatternTestRequest, Body()],
    current_user: User = Security(get_current_user),
) -> ProbandIdPatternTestResult:
    # Stateless by design: no study is loaded and nothing is persisted. Auth is only a
    # generic authenticated-user check because there is no per-study resource to scope to;
    # this endpoint merely compiles a regex and runs fullmatch on a sample string.
    result = core_check_proband_id(
        pattern=body.pattern,
        normalization=body.normalization,
        configured_error_text=None,
        raw_proband_external_id=body.sample,
    )
    return ProbandIdPatternTestResult(
        valid=result.valid,
        normalized_sample=result.normalized,
        error_text=result.error_text,
        pattern_compiles=result.pattern_compiles,
    )


@fast_api_study_router.delete(
    "/study/{study_id}",
    description=f"Delete existing study - Not Yet Implented",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": None},
    },
)
async def delete_study(
    study_id: Annotated[str, Path()],
    current_user_is_admin: User = Security(user_is_admin),
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deleting a study is not yet implented",
    )
    # not implemented. Do we need that? For a multi study instance propably.
    # That would be a whole process -> delete permissions, events,interviews, intakes. More something for a background task.
    # "a mark for deletion" property and a grace period of one day. or an validation by email  would make sense to prevent accidentaly deletion.
    return await study_crud.delete(study_id=study_id)
