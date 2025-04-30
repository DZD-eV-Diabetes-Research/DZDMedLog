from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc, and_
from sqlalchemy.sql.operators import is_not, is_
from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.event import Event
from medlogserver.model.interview import (
    Interview,
    InterviewCreate,
    InterviewUpdate,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface


log = get_logger()
config = Config()


class InterviewCRUD(
    create_crud_base(
        table_model=Interview,
        read_model=Interview,
        create_model=InterviewCreate,
        update_model=InterviewUpdate,
    )
):
    async def list(
        self,
        filter_event_id: str = None,
        filter_proband_external_id: str = None,
        filter_study_id: str = None,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[Interview]:
        query = select(Interview)
        if filter_study_id:
            query = query.join(Event).where(Event.study_id == filter_study_id)
        if filter_event_id:
            query = query.where(Interview.event_id == filter_event_id)
        if filter_proband_external_id:
            query = query.where(
                Interview.proband_external_id == filter_proband_external_id
            )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get_last_by_proband(
        self,
        study_id: str | uuid.UUID,
        proband_external_id: str,
        completed: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Interview]:

        query = (
            select(Interview)
            .join(Event)
            .where(
                and_(
                    Interview.proband_external_id == proband_external_id,
                    Event.study_id == study_id,
                )
            )
        )
        if completed:
            query = (
                query.where(is_not(Interview.interview_end_time_utc, None))
                .order_by(desc(Event.order_position))
                .order_by(desc(Interview.interview_start_time_utc))
                .limit(1)
            )
        else:
            # ToDo: actually we should sort by a `updated_at` field here and not by interview_start_time_utc. but that is not implepentedyet
            query = (
                query.where(is_(Interview.interview_end_time_utc, None))
                .order_by(desc(Event.order_position))
                .order_by(desc(Interview.interview_start_time_utc))
                .limit(1)
            )

        results = await self.session.exec(statement=query)
        interview: Interview | None = results.first()
        if interview is None and raise_exception_if_none:
            raise raise_exception_if_none
        return interview

    async def assert_belongs_to_study(
        self,
        interview_id: str | UUID,
        study_id: str | UUID,
        raise_exception_if_not=None,
    ) -> bool:
        query = (
            select(Event)
            .join(Interview)
            .where(and_(Event.study_id == study_id, Interview.id == interview_id))
        )
        log.debug(f"##query: {query}")
        results = await self.session.exec(statement=query)

        event: Event | None = results.first()
        log.debug(f"##query: {query} \nRESULT: {event}")
        if event is None:
            if raise_exception_if_not:
                raise raise_exception_if_not
            return False
        return True
