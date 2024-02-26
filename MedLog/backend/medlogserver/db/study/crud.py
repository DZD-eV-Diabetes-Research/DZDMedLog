from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.study.model import Study, StudyCreate, StudyUpdate
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()


class StudyCRUD(CRUDBase[Study, Study, StudyCreate, StudyUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        show_deactivated: bool = False,
        pagination: PageParams = None,
    ) -> Sequence[Study]:
        query = select(Study)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        study_id: str | UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Study]:
        query = select(Study).where(Study.id == study_id)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)

        results = await self.session.exec(statement=query)
        user: Study | None = results.one_or_none()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_by_name(
        self,
        study_name: str,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Study]:
        query = select(Study).where(Study.name == study_name)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)

        results = await self.session.exec(statement=query)
        study: Study | None = results.one_or_none()
        if study is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study

    async def create(
        self,
        study_create: StudyCreate,
        raise_exception_if_exists: Exception = None,
    ) -> Study:
        log.debug(f"Create study: {study_create}")

        existing_study: Study = await self.get_by_name(
            study_create.name, show_deactivated=True
        )
        if existing_study and raise_exception_if_exists:
            raise raise_exception_if_exists
        elif existing_study:
            return existing_study
        new_study: Study = Study.model_validate(study_create)
        self.session.add(new_study)
        await self.session.commit()
        await self.session.refresh(new_study)
        return new_study

    async def disable(
        self,
        study_id: str | UUID,
        raise_exception_if_not_exists=None,
        raise_exception_if_allready_deactivated=None,
    ) -> bool:
        study = await self.get(
            study_id=study_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if study.deactivated and raise_exception_if_allready_deactivated:
            raise raise_exception_if_allready_deactivated
        study.deactivated = True
        self.session.add(study)
        await self.session.commit()
        await self.session.refresh(study)
        return study
