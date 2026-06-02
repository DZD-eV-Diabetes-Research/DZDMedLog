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
    and_,
)
from datetime import datetime
import uuid
from uuid import UUID


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.db.user import User
from medlogserver.model.study import Study
from medlogserver.model.study_permission import (
    StudyPermisson,
    StudyPermissonUpdate,
    StudyPermissionRead,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StudyPermissonCRUD(
    create_crud_base(
        table_model=StudyPermisson,
        read_model=StudyPermissionRead,
        create_model=StudyPermisson,
        update_model=StudyPermissonUpdate,
    )
):
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
        pagination: Optional[QueryParamsInterface] = None,
    ) -> List[StudyPermisson]:
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
        user_id: uuid.UUID,
        study_id: uuid.UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[StudyPermisson]:
        query = select(StudyPermisson).where(
            and_(StudyPermisson.study_id == study_id, StudyPermisson.user_id == user_id)
        )
        results = await self.session.exec(statement=query)
        study_permission: StudyPermisson | None = results.one_or_none()
        if study_permission is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study_permission

    async def update_or_create_if_not_exists(
        self,
        user_id: uuid.UUID,
        study_id: uuid.UUID,
        study_permission: StudyPermissonUpdate | StudyPermisson,
    ) -> StudyPermisson:
        existing_study_permission: StudyPermisson = await self.get_by_user_and_study(
            study_id=study_id,
            user_id=user_id,
        )
        log.debug(("existing_study_permission", existing_study_permission))
        explicitly_set = set(study_permission.model_dump(exclude_unset=True).keys())
        if existing_study_permission:
            for key, val in study_permission.model_dump(exclude_unset=True).items():
                if key in StudyPermissonUpdate.model_fields.keys():
                    setattr(existing_study_permission, key, val)
            # User manager is explicitly setting flags → strip OIDC ownership so OIDC
            # will not revoke them on a future login.
            permission_flags = {"is_study_viewer", "is_study_interviewer", "is_study_admin"}
            flags_taken_over = explicitly_set & permission_flags
            if flags_taken_over and existing_study_permission.oidc_managed_permissions:
                existing_study_permission.oidc_managed_permissions = [
                    p for p in existing_study_permission.oidc_managed_permissions
                    if p not in flags_taken_over
                ]
            study_permission = existing_study_permission
        elif isinstance(study_permission, StudyPermissonUpdate):
            study_permission = StudyPermisson(
                user_id=user_id,
                study_id=study_id,
                **study_permission.model_dump(exclude_unset=True),
            )
        self.session.add(study_permission)
        await self.session.commit()
        await self.session.refresh(study_permission)
        return study_permission

    async def oidc_set_permissions(
        self,
        user_id: uuid.UUID,
        study_id: uuid.UUID,
        oidc_managed_flags: set,
        valid_granted: set,
    ) -> StudyPermisson | None:
        """Apply OIDC-derived permissions for one study, preserving manually-set flags.

        oidc_managed_flags: all permission flags OIDC is configured to manage for this study.
        valid_granted: subset of oidc_managed_flags that OIDC currently wants to grant (True).

        Rules:
        - A flag is OIDC-owned if it is in oidc_managed_permissions on the existing record.
        - OIDC can claim a flag (add to oidc_managed_permissions) only if it is currently
          False — i.e., the user manager has not granted it independently.
        - OIDC revokes only flags it owns (present in oidc_managed_permissions).
        - After every change, a record with all flags False is deleted.
        """
        existing = await self.get_by_user_and_study(user_id=user_id, study_id=study_id)
        previously_oidc_owned = set(existing.oidc_managed_permissions if existing else [])

        flags_to_grant: set = set()
        flags_to_revoke: set = set()

        for flag in oidc_managed_flags:
            currently_true = existing is not None and getattr(existing, flag, False)
            oidc_owns = flag in previously_oidc_owned
            wants_to_grant = flag in valid_granted

            if wants_to_grant:
                if not currently_true:
                    # Flag is False — OIDC can claim and set it.
                    flags_to_grant.add(flag)
                elif oidc_owns:
                    # OIDC already owns a True flag — keep claiming it.
                    flags_to_grant.add(flag)
                # else: True but user-manager-owned — don't touch.
            else:
                if oidc_owns:
                    # OIDC owned this but the group is gone — revoke.
                    flags_to_revoke.add(flag)
                # else: not OIDC's flag — don't touch.

        if not flags_to_grant and not flags_to_revoke:
            return existing  # Nothing changed.

        new_oidc_owned = (previously_oidc_owned | flags_to_grant) - flags_to_revoke

        if existing is None:
            if not flags_to_grant:
                return None
            record = StudyPermisson(
                user_id=user_id,
                study_id=study_id,
                oidc_managed_permissions=list(new_oidc_owned),
                **{f: True for f in flags_to_grant},
            )
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)
            return record

        for flag in flags_to_grant:
            setattr(existing, flag, True)
        for flag in flags_to_revoke:
            setattr(existing, flag, False)
        existing.oidc_managed_permissions = list(new_oidc_owned)

        all_permission_flags = {"is_study_viewer", "is_study_interviewer", "is_study_admin"}
        if not any(getattr(existing, p, False) for p in all_permission_flags):
            await self.session.delete(existing)
            await self.session.commit()
            return None

        self.session.add(existing)
        await self.session.commit()
        await self.session.refresh(existing)
        return existing

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

    async def delete_by_user_and_study(
        self, user_id: str | UUID, study_id: str | UUID
    ) -> bool:
        query = delete(StudyPermisson).where(
            and_(StudyPermisson.user_id == user_id, StudyPermisson.study_id == study_id)
        )
        await self.session.exec(statement=query)
        await self.session.commit()
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
