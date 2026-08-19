from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel
from sqlalchemy.exc import IntegrityError

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.study import (
    Study,
    StudyCreate,
    StudyCreateAPI,
    StudyUpdate,
)
from medlogserver.model.event import Event, EventCreate
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
        pagination: Optional[QueryParamsInterface] = None,
    ) -> List[Study]:
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
        log.debug(f"study {study}")
        if study is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study

    async def get_by_name(
        self,
        study_name: str,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Study]:
        query = select(Study).where(Study.display_name == study_name)
        if not show_deactivated:
            query = query.where(Study.deactivated == False)

        results = await self.session.exec(statement=query)
        study: Study | None = results.one_or_none()
        if study is None and raise_exception_if_none:
            raise raise_exception_if_none
        return study

    async def clone(
        self,
        source_study: Study,
        new_display_name: str,
        raise_custom_exception_if_exists: Optional[Exception] = None,
    ) -> Study:
        """Create a new study from an existing one: same configuration, same event structure.

        Copied is everything that makes up the *setup* of the source study - all
        `StudyCreateAPI` fields (proband ID pattern/error text/normalization/example and
        the `no_permissions` flag) plus one new event per source event, keeping name and
        `order_position`. Deriving the copied fields from `StudyCreateAPI` (instead of an
        explicit list) means future study-setup fields are cloned automatically.

        Explicitly *not* copied: collected data (interviews, intakes) and study
        permissions - a clone starts empty and, like a freshly created study, is only
        accessible to instance admins until permissions are granted. The clone is always
        created as active, even when the source study is deactivated.

        Study and events are written in a single transaction, so a name collision can not
        leave a half-cloned study behind.
        """
        cloned_setup = source_study.model_dump(
            include=set(StudyCreateAPI.model_fields.keys())
        )
        cloned_setup["display_name"] = new_display_name
        new_study = Study.model_validate(StudyCreate(**cloned_setup))
        self.session.add(new_study)

        source_events_query = (
            select(Event)
            .where(Event.study_id == source_study.id)
            .order_by(Event.order_position)
        )
        source_events: List[Event] = (
            await self.session.exec(source_events_query)
        ).all()
        for source_event in source_events:
            self.session.add(
                Event.model_validate(
                    EventCreate(
                        name=source_event.name,
                        order_position=source_event.order_position,
                        study_id=new_study.id,
                    )
                )
            )

        try:
            await self.session.commit()
        except IntegrityError as err:
            await self.session.rollback()
            if raise_custom_exception_if_exists:
                raise raise_custom_exception_if_exists
            raise err
        await self.session.refresh(new_study)
        log.debug(
            f"Cloned study '{source_study.display_name}' ({source_study.id}) into "
            f"'{new_study.display_name}' ({new_study.id}) with {len(source_events)} event(s)"
        )
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
