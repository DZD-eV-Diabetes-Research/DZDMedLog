import uuid
from typing import List, Literal, Annotated
from fastapi import HTTPException, status, Security, Depends, Path

# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger

from medlogserver.db.user.user import User

from medlogserver.api.auth.base import get_current_user
from medlogserver.config import Config
from medlogserver.db.study.study_permission import StudyPermisson
from medlogserver.db.study.study import Study, StudyCRUD, get_study_crud
from medlogserver.db.study.study_permission import (
    StudyPermisson,
    StudyPermissonCRUD,
    get_study_permission_crud,
)
from medlogserver.db.interview.interview import InterviewCRUD
from medlogserver.db.event.event import EventCRUD

config = Config()

from medlogserver.log import get_logger

log = get_logger()


class UserStudyAccess:
    def __init__(self, user: User, study: Study, perm: StudyPermisson):
        self.user = user
        self.study = study
        self.user_study_perm = perm

    def user_has_access(
        self,
        as_role: Literal[None, "admin", "viewer", "interviewer"] = "viewer",
    ):
        if config.ADMIN_ROLE_NAME in self.user.roles:
            return True
        if self.study.no_permissions:
            # the study has access permission switched off. all user have access
            return True
        if self.user_study_perm:
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

    def user_has_interviewer_permission(self):
        self.user_has_access(as_role="interviewer")

    def user_is_admin(self):
        self.user_has_access(as_role="admin")


class UserStudyAccessCollection:
    """A access helper that contains all study and the permissions a certain user has acces to"""

    def __init__(self, user: User):
        self.user = user
        self.studies_access: dict[str, UserStudyAccess] = {}

    async def init(
        self,
        study_permisson_crud: StudyPermissonCRUD = Depends(get_study_permission_crud),
        study_crud: StudyCRUD = Depends(get_study_crud),
        study_id: str | uuid.UUID = None,
    ):
        """Gatheres all studies and permission the user has access to. If a study_id is provided only data fpr this study is gathered.
        Todo: This is a very costly function. Evaluate if a caching mechanism makes sense here

        Args:
            study_permisson_crud (StudyPermissonCRUD, optional): _description_. Defaults to Depends(get_study_permission_crud).
            study_crud (StudyCRUD, optional): _description_. Defaults to Depends(get_study_crud).
            study_id (str | uuid.UUID, optional): _description_. Defaults to None.
        """
        if config.ADMIN_ROLE_NAME in self.user.roles:
            # lets save us all the data gathering. the user is admin. admins are all access
            return
        study_permissions = await study_permisson_crud.list(
            filter_user_id=self.user.id, filter_study_id=study_id
        )
        if study_id:
            studies_data = [await study_crud.get(study_id)]
        else:
            studies_data = await study_crud.list(show_deactivated=True)
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
    ):
        if config.ADMIN_ROLE_NAME in self.user.roles:
            return True
        self.studies_access[study_id].user_has_access(as_role=as_role)

    def user_is_interviewer(self, study_id):
        self.user_has_access_to(study_id=study_id, as_role="interviewer")

    def user_is_admin(self, study_id):
        self.user_has_access_to(study_id=study_id, as_role="admin")


async def user_has_studies_access_map(
    user: Annotated[User, Security(get_current_user)],
) -> UserStudyAccessCollection:
    access_helper = UserStudyAccessCollection(user=user)
    await access_helper.init()
    return access_helper


async def user_has_study_access(
    study_id: Annotated[str, Path()] | uuid.UUID,
    user: Annotated[User, Security(get_current_user)],
) -> UserStudyAccess:
    access_helper = UserStudyAccessCollection(user=user)
    await access_helper.init(study_id=study_id)
    study_access = access_helper.studies_access[study_id]
    if not study_access.user_has_access():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No access to study."
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
