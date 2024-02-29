from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List

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

from medlogserver.api.paginator import PageParams, pagination_query, PaginatedResponse
from medlogserver.db.user.crud import (
    User,
)

from medlogserver.api.auth.base import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)

from medlogserver.db.study.model import Study, StudyUpdate, StudyCreate
from medlogserver.db.study.crud import StudyCRUD
from medlogserver.db.study_permission.model import StudyPermisson
from medlogserver.db.study_permission.crud import StudyPermissonCRUD
from medlogserver.api.routes_app.security import (
    user_has_studies_access_map,
    UserStudyAccessCollection,
)

from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_study_router: APIRouter = APIRouter()


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
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[Study]:

    # ToDo: This is a pretty cost intensive endpoint/query. Would be a good candiate for some kind of cache. UPDATE: now all logic is in Security(user_has_study_access_map) fix/cache that

    # Thought (Tim): the pagination is everything but scalable in this Endpoint, because we fetch all studies, check them for permissions and paginate that result.
    # better would be a pagination on database level.
    # But we can assume that there will never be an MedLog instance that will host more than a couple of studies.
    # so everything is fine...
    all_studies = await study_crud.list(show_deactivated=show_deactived)
    allowed_studies: List[Study] = []

    for study in all_studies:
        if study_permissions_helper.user_has_access_to(study_id=study.id):
            allowed_studies.append(study)

    pageinated_allowed_studies = allowed_studies[pagination.offset : pagination.limit]
    return PaginatedResponse(
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
    study: StudyCreate,
    current_user_is_admin: User = Security(user_is_admin),
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
) -> User:
    return await study_crud.create(
        study,
        raise_custom_exception_if_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Study with name '{study.name}' allready exists",
        ),
    )


@fast_api_study_router.patch(
    "/study/{study_id}",
    response_model=Study,
    description=f"Update existing study",
)
async def update_study(
    study_id: Annotated[str, Path()],
    study: Annotated[
        StudyUpdate, Body(description="The study object with updated data")
    ],
    study_crud: StudyCRUD = Depends(StudyCRUD.get_crud),
    study_permission_crud: StudyPermissonCRUD = Depends(StudyPermissonCRUD.get_crud),
    current_user: User = Security(get_current_user),
) -> Study:
    # security
    not_allowed_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"You are not allowed to update this study",
    )
    passed_security_check: bool = False
    if config.ADMIN_ROLE_NAME in current_user.roles:
        passed_security_check = True
    else:
        perm: StudyPermisson = await study_permission_crud.get_by_user_and_study(
            study_id=study_id,
            user_id=current_user.id,
            raise_exception_if_none=not_allowed_error,
        )
        if perm.is_study_admin:
            passed_security_check = True
    if not passed_security_check:
        raise not_allowed_error
    # creation
    return await study_crud.create(study)


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
