from pydantic import BaseModel, Field

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Annotated, NoReturn
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import (
    HTTPException,
    status,
    Security,
    Depends,
    APIRouter,
    Form,
    Header,
    Query,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    OAuth2AuthorizationCodeBearer,
    OpenIdConnect,
)

#
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.REST_api.auth.tokens import (
    JWTAccessTokenContainer,
    JWTAccessTokenResponse,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.user import get_user_crud, UserCRUD, User
from medlogserver.db.user.user_auth import (
    get_user_auth_crud,
    UserAuthCRUD,
    UserAuth,
    UserAuthCreate,
    get_user_auth_refresh_token_crud,
    UserAuthRefreshTokenCRUD,
    UserAuthRefreshToken,
    AllowedAuthSourceTypes,
)
from medlogserver.REST_api.auth.base import get_current_user, user_is_admin
from medlogserver.config import Config
from medlogserver.db.study.study_permission import StudyPermisson
from medlogserver.db.study.study import Study, StudyCRUD, get_study_crud
from medlogserver.db.study.study_permission import (
    StudyPermisson,
    StudyPermissonCRUD,
    get_study_permission_crud,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


class UserStudyAccess:
    def __init__(self, user: User):
        self.user = user
        self.study_permissions: List[StudyPermisson]
        self.study_data: List[Study]

    async def init(
        self,
        study_permisson_crud: StudyPermissonCRUD = Depends(get_study_permission_crud),
        study_crud: StudyCRUD = Depends(get_study_crud),
    ):
        if config.ADMIN_ROLE_NAME in self.user.roles:
            # lets save all the data gathering. the user is admin. admins are all access
            return
        self.study_permissions = study_permisson_crud.list(filter_user_id=self.user.id)
        self.study_data = study_crud.list(show_deactivated=True)

    def _get_study_data(self, study_id) -> Study:
        for study in self.study_data:
            if study.id == study_id:
                return study

    def _get_study_perm(self, study_id) -> StudyPermisson | None:
        for study_perm in self.study_permissions:
            if study_perm.study_id == study_id:
                return study_perm
        return None

    def user_has_access_to(
        self,
        study_id: str | uuid.UUID,
        as_role: Literal[None, "admin", "viewer", "interviewer"] = "viewer",
    ):
        if config.ADMIN_ROLE_NAME in self.user.roles:
            return True
        study = self._get_study_data(study_id)
        if study.no_permissions:
            # the study has access permission switched off. all user have access
            return True
        study_perm = self._get_study_perm(study_id)
        if study_perm:
            if as_role is None or as_role == "viewer":
                return (
                    study_perm.is_study_admin
                    or study_perm.is_study_interviewer
                    or study_perm.is_study_viewer
                )
            elif as_role == "interviewer":
                return study_perm.is_study_admin or study_perm.is_study_interviewer
            elif as_role == "admin":
                return study_perm.is_study_admin

    def user_is_interviewer(self, study_id):
        self.user_has_access_to(study_id=study_id, as_role="interviewer")

    def user_is_admin(self, study_id):
        self.user_has_access_to(study_id=study_id, as_role="admin")


async def user_has_study_access_map(
    user: Annotated[User, Security(get_current_user)],
) -> UserStudyAccess:
    access_helper = UserStudyAccess(user=user)
    await access_helper.init()
    return access_helper
