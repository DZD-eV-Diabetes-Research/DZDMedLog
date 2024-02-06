from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel
from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.event.event import Event

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.interview_auth import InterviewAuthRefreshTokenCRUD


log = get_logger()
config = Config()


class InterviewCreate(Base, table=False):
    event_id: str = Field(foreign_key="event.id")
    proband_external_id: str = Field()
    interview_start_time_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    interview_end_time_utc: datetime = Field(default=None)
    proband_has_taken_meds: bool = Field()
    interview_number: int = Field(
        description="TB: This field is still kind of mysterious to me. In the user interview video the user just filled it with some number. Maybe a process we can automize (shameless plug: https://git.apps.dzd-ev.org/dzdpythonmodules/ptan)?"
    )


class InterviewUpdate(InterviewCreate, table=False):
    pass


class Interview(InterviewCreate, table=True):
    __tablename__ = "interview"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


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

    async def get_last_completed_by_proband(
        self,
        proband_external_id: str,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Interview]:

        query = select(Interview).where(
            Interview.proband_external_id == proband_external_id
        )

        results = await self.session.exec(statement=query)
        interview: Interview | None = results.one_or_none()
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


async def get_interview_crud(
    session: AsyncSession = Depends(get_async_session),
) -> InterviewCRUD:
    yield InterviewCRUD(session=session)


get_interviews_crud_context = contextlib.asynccontextmanager(get_interview_crud)
