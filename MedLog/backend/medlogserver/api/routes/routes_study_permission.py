from typing import Annotated, Sequence, List, NoReturn, Type
from datetime import datetime, timedelta, timezone


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


from medlogserver.model.study_permission import (
    StudyPermisson,
    StudyPermissionRead,
    StudyPermissonUpdate,
)
from medlogserver.db.study_permission import StudyPermissonCRUD
from medlogserver.config import Config
from medlogserver.api.study_access import (
    user_has_study_access,
    UserStudyAccess,
)
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_permissions_router: APIRouter = APIRouter()

StudyPermissonQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    StudyPermissionRead
)


#############
@fast_api_permissions_router.get(
    "/study/{study_id}/permissions",
    response_model=PaginatedResponse[StudyPermissionRead],
    description=f"List all access permissons for a study. User must be system admin, system user manager or study admin to see these.",
)
async def list_study_permissions(
    study_access: UserStudyAccess = Security(user_has_study_access),
    permission_crud: StudyPermissonCRUD = Depends(StudyPermissonCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(StudyPermissonQueryParams),
) -> PaginatedResponse[StudyPermissionRead]:
    if not study_access.user_can_manage_study_permissions():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to manage study permissions",
        )
    result_items = await permission_crud.list(
        filter_study_id=study_access.study.id, pagination=pagination
    )
    return PaginatedResponse(
        total_count=await permission_crud.count(filter_study_id=study_access.study.id),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )


############
@fast_api_permissions_router.get(
    "/study/{study_id}/permissions/{permission_id}",
    response_model=StudyPermisson,
    description=f"List all medicine intakes of one probands last completed interview.",
)
async def get_permission_details(
    permission_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    permission_crud: StudyPermissonCRUD = Depends(StudyPermissonCRUD.get_crud),
) -> StudyPermisson:
    if not study_access.user_can_manage_study_permissions():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to manage study permissions",
        )
    # bleimehl: SECURITY WARNING: in theory a study admin from one study, who could obtain a permission UUID from another study,
    # could manipulate permission from that other study without permission.
    # determined as low risk, at the moment we can assumes that registered admins are not malicious actors
    # and to obtain that other UUID its need some criminal energy :) .
    # ToDo: include a check if that permission really belongs to the study
    return await permission_crud.get(permission_id)


@fast_api_permissions_router.put(
    "/study/{study_id}/permissions/{user_id}",
    response_model=StudyPermissonUpdate,
    description=f"Create or update new study permision for a user.",
)
async def create_or_update_permission(
    user_id: str,
    study_perm: StudyPermissonUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    permission_crud: StudyPermissonCRUD = Depends(StudyPermissonCRUD.get_crud),
) -> StudyPermisson:
    if not study_access.user_can_manage_study_permissions():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to manage study permissions",
        )
    perm = StudyPermisson(user_id=user_id, study_id=study_access.study.id, **study_perm)
    return await permission_crud.update_or_create_if_not_exists(perm)
