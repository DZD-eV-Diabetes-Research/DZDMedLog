from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import (
    Field,
    select,
    delete,
    Column,
    JSON,
    SQLModel,
    UniqueConstraint,
    func,
)
from datetime import datetime
import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.user.crud import User
from medlogserver.db.study.model import Study
from medlogserver.db.study_permission.model import (
    StudyPermisson,
    StudyPermissonUpdate,
    StudyPermissionRead,
)
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StudyPermissonCRUD(
    CRUDBase[
        StudyPermisson,
        StudyPermissionRead,
        StudyPermisson,
        StudyPermissonUpdate,
    ]
):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count(
        self,
        filter_study_id: uuid.UUID | str = None,
        filter_user_id: uuid.UUID | str = None,
    ) -> int:
        query = select(func.count()).select_from(StudyPermisson)
        if filter_study_id:
            query = query.where(StudyPermisson.study_id == filter_study_id)
        if filter_user_id:
            query = query.where(StudyPermisson.user_id == filter_user_id)
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        filter_study_id: uuid.UUID | str = None,
        filter_user_id: uuid.UUID | str = None,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[StudyPermisson]:
        query = select(StudyPermisson)
        if filter_study_id:
            query = query.where(StudyPermisson.study_id == filter_study_id)
        if filter_user_id:
            query = query.where(StudyPermisson.user_id == filter_user_id)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        study_permission_id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[StudyPermisson]:
        query = select(StudyPermisson).where(StudyPermisson.id == study_permission_id)
        results = await self.session.exec(statement=query)
        study_permission: StudyPermisson | None = results.one_or_none()
        if study_permission is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study_permission

    async def get_by_user_and_study(
        self,
        user_id: uuid.UUID | str,
        study_id: uuid.UUID | str,
        raise_exception_if_none: Exception = None,
    ) -> Optional[StudyPermisson]:
        query = select(StudyPermisson).where(
            StudyPermisson.id == study_id and StudyPermisson.user_id == user_id
        )
        results = await self.session.exec(statement=query)
        study_permission: StudyPermisson | None = results.one_or_none()
        if study_permission is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study_permission

    async def update_or_create_if_not_exists(
        self, study_permission=StudyPermisson
    ) -> StudyPermisson:
        existing_study_permission: StudyPermisson = await self.list(
            filter_study_id=study_permission.study_id,
            filter_user_id=study_permission.user_id,
        )
        if existing_study_permission:
            for k in StudyPermissonUpdate.model_fields.keys():
                setattr(existing_study_permission, k, getattr(study_permission, k))
            study_permission = existing_study_permission
        self.session.add(study_permission)
        await self.session.commit()
        await self.session.refresh(study_permission)
        return study_permission

    # I tested if we can remove this. looks like. todo: remove this func
    async def create_REMOVE_ME(
        self,
        study_permission: StudyPermisson,
        raise_custom_exception_if_exists: Exception = None,
    ) -> StudyPermisson:
        log.debug(
            f"Create study permission for user {study_permission.user_id} in study {study_permission.study_id}"
        )
        existing_study_permission: StudyPermisson = await self.list(
            filter_study_id=study_permission.study_id,
            filter_user_id=study_permission.user_id,
        )
        if existing_study_permission and raise_custom_exception_if_exists:
            raise raise_custom_exception_if_exists
        elif existing_study_permission:
            return existing_study_permission
        self.session.add(study_permission)
        await self.session.commit()
        await self.session.refresh(study_permission)
        return study_permission

    async def update(
        self,
        study_permission: StudyPermisson,
        study_permission_id: str | UUID = None,
        raise_exception_if_not_exists=None,
    ) -> StudyPermisson:
        study_permission_id = (
            study_permission_id if study_permission_id else study_permission.id
        )

        if study_permission_id is None:
            raise ValueError(
                "StudyPermisson update failed, uuid must be set in study_permission object or passed as argument `study_permission_id`"
            )
        study_permission_from_db = await self.get(
            study_permission_id=study_permission_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        for k, v in study_permission.model_dump(exclude_unset=True).items():
            if k in StudyPermisson.model_fields.keys():
                setattr(study_permission_from_db, k, v)
        self.session.add(study_permission_from_db)
        await self.session.commit()
        await self.session.refresh(study_permission_from_db)
        return study_permission_from_db

    async def delete_by_user(self, user_id: str | UUID):
        """This delete function can be used to remove all permissions a user have. That can be usefull when an account is deleted.

        Args:
            user_id (str | UUID): _description_
            study_id (str | UUID, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_

        Returns:
            StudyPermisson: _description_
        """

        query = delete(StudyPermisson).where(StudyPermisson.user_id == user_id)
        await self.session.exec(statement=query)
        return True

    async def delete_by_study(self, study_id: str | UUID):
        """This delete function can be used to remove all permissions to a certain study. This can be helpfull if a study will be archived.
        WARNING: Only admin accounts can access the study afterwards.

        Args:
            user_id (str | UUID): _description_
            study_id (str | UUID, optional): _description_. Defaults to None.

        Raises:
            ValueError: _description_

        Returns:
            StudyPermisson: _description_
        """

        query = delete(StudyPermisson).where(StudyPermisson.study_id == study_id)
        await self.session.exec(statement=query)
        return True
