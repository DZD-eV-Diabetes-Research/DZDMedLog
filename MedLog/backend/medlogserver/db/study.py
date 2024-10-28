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
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.study import Study, StudyCreate, StudyUpdate
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class StudyCRUD(
    create_crud_base(
        table_model=Study,
        read_model=Study,
        create_model=StudyCreate,
        update_model=StudyUpdate,
    )
):

    async def list(
        self,
        show_deactivated: bool = False,
        pagination: QueryParamsInterface = None,
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
        study: Study | None = results.one_or_none()
        log.info(f"study {study}")
        if study is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study

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
