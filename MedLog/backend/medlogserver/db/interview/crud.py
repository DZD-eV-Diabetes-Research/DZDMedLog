from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from sqlalchemy.sql.operators import is_not, is_
from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.event.model import Event
from medlogserver.db.interview.model import Interview, InterviewCreate, InterviewUpdate
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import PageParams


log = get_logger()
config = Config()


class InterviewCRUD(CRUDBase[Interview, Interview, InterviewCreate, InterviewUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_event_id: str = None,
        filter_by_proband_external_id: str = None,
        filter_by_study_id: str = None,
        pagination: PageParams = None,
    ) -> Sequence[Interview]:
        query = select(Interview)
        if filter_by_study_id:
            query = query.join(Event).where(Event.study_id == filter_by_study_id)
        if filter_by_event_id:
            query = query.where(Interview.event_id == filter_by_event_id)
        if filter_by_proband_external_id:
            query = query.where(
                Interview.proband_external_id == filter_by_proband_external_id
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
                Interview.proband_external_id == proband_external_id
                and Event.study_id == study_id
            )
        )
        if completed:
            query = (
                query.where(is_not(Interview.interview_end_time_utc, None))
                .order_by(desc(Interview.interview_end_time_utc))
                .limit(1)
            )
        else:
            # ToDo: actually we should sort by a `updated_at` field here and not by interview_start_time_utc. but that is not implepentedyet
            query = (
                query.where(is_(Interview.interview_end_time_utc, None))
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
            .where(
                Event.id == Interview.event_id
                and Event.study_id == study_id
                and Interview.id == interview_id
            )
        )
        results = await self.session.exec(statement=query)
        event: Event | None = results.first()
        if event is None:
            if raise_exception_if_not:
                raise raise_exception_if_not
            return False
        return True
