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
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.api.auth.tokens import (
    JWTBundleTokenResponse,
    JWTAccessTokenContainer,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.user import (
    get_user_crud,
    User,
    UserCRUD,
    UserCreate,
    UserUpdate,
    UserUpdateByUser,
    UserUpdateByAdmin,
)
from medlogserver.db.user.user_auth import (
    get_user_auth_crud,
    UserAuth,
    UserAuthCreate,
    UserAuthUpdate,
    UserAuthCRUD,
    UserAuthRefreshToken,
    UserAuthRefreshTokenCreate,
    UserAuthRefreshTokenCRUD,
    get_user_auth_refresh_token_crud,
    AllowedAuthSourceTypes,
)
from medlogserver.api.auth.base import (
    TOKEN_ENDPOINT_PATH,
    oauth2_scheme,
    user_is_admin,
    user_is_usermanager,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)

from medlogserver.db.event.model import Event, EventUpdate
from medlogserver.db.event.crud import EventCRUD, get_event_crud

from medlogserver.db.study_permission.model import (
    StudyPermisson,
    StudyPermissonHumanReadeable,
    StudyPermissonUpdate,
)
from medlogserver.db.study_permission.crud import (
    StudyPermissonCRUD,
    get_study_permission_crud,
)

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)
from medlogserver.config import Config
from medlogserver.db.interview.model import (
    Interview,
    InterviewCreate,
    InterviewUpdate,
)
from medlogserver.db.interview.crud import InterviewCRUD, get_interview_crud
from medlogserver.db.intake.model import (
    Intake,
    IntakeCreate,
    IntakeUpdate,
)
from medlogserver.db.intake.crud import IntakeCRUD, get_intake_crud
from medlogserver.api.routes_app.security import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    UserStudyAccessCollection,
    assert_interview_id_is_part_of_study_id,
)
from medlogserver.api.base import HTTPMessage

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_permissions_router: APIRouter = APIRouter()


#############
@fast_api_permissions_router.get(
    "/study/{study_id}/permissions",
    response_model=List[StudyPermisson | StudyPermissonHumanReadeable],
    description=f"List all access permissons for a study. User must be system admin, system user manager or study admin to see these.",
)
async def list_study_permissions(
    human_readable: Annotated[
        bool,
        Query(
            description="When set to true, includes user names and study names. which are not part of the table. This can be handy when generating overview lists in the UI.",
        ),
    ] = False,
    study_access: UserStudyAccess = Security(user_has_study_access),
    permission_crud: StudyPermissonCRUD = Depends(get_study_permission_crud),
) -> List[StudyPermisson | StudyPermissonHumanReadeable]:
    if not study_access.user_can_manage_study_permissions():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to manage study permissions",
        )
    if human_readable:
        return await permission_crud.list_human_readable(
            filter_study_id=study_access.study.id
        )
    return await permission_crud.list(filter_study_id=study_access.study.id)


############
@fast_api_permissions_router.get(
    "/study/{study_id}/permissions/{permission_id}",
    response_model=StudyPermisson,
    description=f"List all medicine intakes of one probands last completed interview.",
)
async def list_all_intakes_of_last_uncompleted_interview(
    permission_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    permission_crud: StudyPermissonCRUD = Depends(get_study_permission_crud),
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
    permission_crud: StudyPermissonCRUD = Depends(get_study_permission_crud),
) -> StudyPermisson:
    if not study_access.user_can_manage_study_permissions():
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to manage study permissions",
        )
    perm = StudyPermisson(
        user_id=user_id, study_id=study_access.study.id, **StudyPermissonUpdate
    )
    return await permission_crud.update_or_create_if_not_exists(perm)
