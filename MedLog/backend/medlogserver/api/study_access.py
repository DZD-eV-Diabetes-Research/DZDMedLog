import uuid
from typing import List, Literal, Annotated
from fastapi import HTTPException, status, Security, Depends, Path

# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger

from medlogserver.db.user import User
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.config import Config
from medlogserver.model.study_permission import StudyPermisson
from medlogserver.model.study import Study
from medlogserver.db.study import StudyCRUD
from medlogserver.model.study_permission import StudyPermisson
from medlogserver.db.study_permission import StudyPermissonCRUD
from medlogserver.db.interview import InterviewCRUD

from medlogserver.db.event import EventCRUD

config = Config()

from medlogserver.log import get_logger

log = get_logger()


class UserStudyAccess:
    def __init__(self, user: User, study: Study, perm: StudyPermisson = None):
        self.user = user
        self.study = study
        self.user_study_perm = perm

    def user_has_access(
        self,
        as_role: Literal[None, "admin", "viewer", "interviewer"] = "viewer",
    ):
        if self.user.is_admin():
            return True
        elif self.study.no_permissions:
            # the study has access permission switched off. all user have access
            return True
        elif self.user_study_perm:
            if as_role is None or as_role == "viewer":
                return (
                    self.user_study_perm.is_study_admin
                    or self.user_study_perm.is_study_interviewer
                    or self.user_study_perm.is_study_viewer
                )
            elif as_role == "interviewer":
                return (
                    self.user_study_perm.is_study_admin
                    or self.user_study_perm.is_study_interviewer
                )
            elif as_role == "admin":
                return self.user_study_perm.is_study_admin

    def user_has_interviewer_permission(self) -> bool:
        return self.user_has_access(as_role="interviewer")

    def user_is_study_admin(self) -> bool:
        return self.user_has_access(as_role="admin")

    def user_can_manage_study_permissions(self) -> bool:
        if self.user.is_usermanager() or self.user_is_study_admin():
            return True
        return False


class UserStudyAccessCollection:
    """A access helper that contains all study and the permissions a certain user has acces to"""

    def __init__(self, user: User):
        self.user = user
        self.studies_access: dict[str, UserStudyAccess] = {}

    async def init(
        self,
        study_permisson_crud: StudyPermissonCRUD,
        study_crud: StudyCRUD,
        study_id: str | uuid.UUID = None,
    ):
        """Gatheres all studies and permission the user has access to. If a study_id is provided only data fpr this study is gathered.
        Todo: This is a very costly function. Evaluate if a caching mechanism makes sense here

        Args:
            study_permisson_crud (StudyPermissonCRUD, optional): _description_. Defaults to Depends(StudyPermissonCRUD.get_crud).
            study_crud (StudyCRUD, optional): _description_. Defaults to Depends(StudyCRUD.get_crud).
            study_id (str | uuid.UUID, optional): _description_. Defaults to None.
        """

        if study_id:
            studies_data = [await study_crud.get(study_id)]
        else:
            studies_data = await study_crud.list(show_deactivated=True)
        if self.user.is_usermanager():
            # lets save us permission data gathering. the user is admin. admins are all access
            for study in studies_data:
                if study is not None:
                    self.studies_access[study.id] = UserStudyAccess(
                        self.user, study, None
                    )
            return

        study_permissions = await study_permisson_crud.list(
            filter_user_id=self.user.id, filter_study_id=study_id
        )
        for study_perm in study_permissions:
            study = next(
                (s.id for s in studies_data if s.id == study_perm.study_id), None
            )
            if study:
                self.studies_access[study_perm.study_id] = UserStudyAccess(
                    self.user, study, study_perm
                )

    def user_has_access_to(
        self,
        study_id: str | uuid.UUID,
        as_role: Literal[None, "admin", "viewer", "interviewer"] = None,
    ) -> bool:
        if self.user.is_admin():
            return True
        self.studies_access[study_id].user_has_access(as_role=as_role)

    def user_is_interviewer(self, study_id) -> bool:
        self.user_has_access_to(study_id=study_id, as_role="interviewer")

    def user_is_admin(self, study_id) -> bool:
        self.user_has_access_to(study_id=study_id, as_role="admin")


async def user_has_studies_access_map(
    user: Annotated[User, Security(get_current_user)],
    study_permisson_crud: Annotated[
        StudyPermissonCRUD, Depends(StudyPermissonCRUD.get_crud)
    ],
    study_crud: Annotated[StudyCRUD, Depends(StudyCRUD.get_crud)],
) -> UserStudyAccessCollection:
    access_helper = UserStudyAccessCollection(user=user)
    await access_helper.init(
        study_crud=study_crud, study_permisson_crud=study_permisson_crud
    )
    return access_helper


async def user_has_study_access(
    study_id: str | uuid.UUID,
    user: Annotated[User, Security(get_current_user)],
    study_permisson_crud: Annotated[
        StudyPermissonCRUD, Depends(StudyPermissonCRUD.get_crud)
    ],
    study_crud: Annotated[StudyCRUD, Depends(StudyCRUD.get_crud)],
) -> UserStudyAccess:
    if isinstance(study_id, str):
        study_id: uuid.UUID = uuid.UUID(study_id)
    access_helper = UserStudyAccessCollection(user=user)
    await access_helper.init(
        study_id=study_id,
        study_crud=study_crud,
        study_permisson_crud=study_permisson_crud,
    )
    try:
        study_access = access_helper.studies_access[study_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study with id {study_id} does not exist.",
        )
    if not study_access.user_has_access():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"No access to study {study_id}.",
        )
    return study_access


async def assert_interview_id_is_part_of_study_id(
    study_id: str,
    interview_id: str,
    interview_crud: InterviewCRUD,
):
    # todo: another candiate for caching
    return await interview_crud.assert_belongs_to_study(
        interview_id=interview_id, study_id=study_id
    )
