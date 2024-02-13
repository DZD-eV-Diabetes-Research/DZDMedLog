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
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.event.model import Event
from medlogserver.db.interview.model import Interview, InterviewCreate, InterviewUpdate


log = get_logger()
config = Config()


class InterviewCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_event_id: str = None,
        filter_by_proband_external_id: str = None,
        filter_by_study_id: str = None,
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
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        interview_id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Interview]:
        query = select(Interview).where(Interview.id == interview_id)
        results = await self.session.exec(statement=query)
        interview: Interview | None = results.one_or_none()
        if interview is None and raise_exception_if_none:
            raise raise_exception_if_none
        return interview

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

    async def create(
        self,
        interview: InterviewCreate | Interview,
    ) -> Interview:
        log.debug(f"Create interview: {interview}")
        self.session.add(interview)
        await self.session.commit()
        await self.session.refresh(interview)
        return interview

    async def update(
        self,
        interview_id: str | UUID,
        interview_update: InterviewUpdate,
        raise_exception_if_not_exists=None,
    ) -> Interview:
        interview_from_db = await self.get(
            interview_id=interview_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        for k, v in interview_update.model_dump(exclude_unset=True).items():
            if k in InterviewUpdate.model_fields.keys():
                setattr(interview_from_db, k, v)
        self.session.add(interview_from_db)
        await self.session.commit()
        await self.session.refresh(interview_from_db)
        return interview_from_db

    async def delete(
        self,
        interview_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> bool:
        interview = await self.get(
            interview_id=interview_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if interview is not None:
            delete(interview).where(Interview.id == interview_id)
        return True

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


async def get_interview_crud(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[InterviewCRUD, None]:
    yield InterviewCRUD(session=session)


get_interviews_crud_context = contextlib.asynccontextmanager(get_interview_crud)
