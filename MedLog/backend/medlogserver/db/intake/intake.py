from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
import enum
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
# from medlogserver.db.intake_auth import IntakeAuthRefreshTokenCRUD


log = get_logger()
config = Config()

AdministeredByDoctorAnswers = enum.Enum(
    "AdministeredByDoctorAnswers", config.APP_CONFIG_PRESCRIBED_BY_DOC_ANSWERS
)


class IntakeCreate(Base, table=False):
    interview_id: str = Field(foreign_key="interview.id")
    intake_start_time_utc: datetime = Field()
    intake_end_time_utc: datetime = Field(default=None)
    administered_by_doctor: AdministeredByDoctorAnswers


class IntakeUpdate(IntakeCreate, table=False):
    pass


class Intake(IntakeCreate, table=True):
    __tablename__ = "intake"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class IntakeCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_event_id: str = None,
        filter_by_proband_external_id: str = None,
        filter_by_study_id: str = None,
    ) -> Sequence[Intake]:
        query = select(Intake)
        if filter_by_study_id:
            query = query.join(Event).where(Event.study_id == filter_by_study_id)
        if filter_by_event_id:
            query = query.where(Intake.event_id == filter_by_event_id)
        if filter_by_proband_external_id:
            query = query.where(
                Intake.proband_external_id == filter_by_proband_external_id
            )
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        intake_id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Intake]:
        query = select(Intake).where(Intake.id == intake_id)
        results = await self.session.exec(statement=query)
        intake: Intake | None = results.one_or_none()
        if intake is None and raise_exception_if_none:
            raise raise_exception_if_none
        return intake

    async def get_last_completed_by_proband(
        self,
        proband_external_id: str,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Intake]:

        query = select(Intake).where(Intake.proband_external_id == proband_external_id)

        results = await self.session.exec(statement=query)
        intake: Intake | None = results.one_or_none()
        if intake is None and raise_exception_if_none:
            raise raise_exception_if_none
        return intake

    async def create(
        self,
        intake: IntakeCreate | Intake,
    ) -> Intake:
        log.debug(f"Create intake: {intake}")
        self.session.add(intake)
        await self.session.commit()
        await self.session.refresh(intake)
        return intake

    async def update(
        self,
        intake_id: str | UUID,
        intake_update: IntakeUpdate,
        raise_exception_if_not_exists=None,
    ) -> Intake:
        intake_from_db = await self.get(
            intake_id=intake_id,
            raise_exception_if_none=raise_exception_if_not_exists,
        )
        for k, v in intake_update.model_dump(exclude_unset=True).items():
            if k in IntakeUpdate.model_fields.keys():
                setattr(intake_from_db, k, v)
        self.session.add(intake_from_db)
        await self.session.commit()
        await self.session.refresh(intake_from_db)
        return intake_from_db

    async def delete(
        self,
        intake_id: str | UUID,
        raise_exception_if_not_exists=None,
    ) -> bool:
        intake = await self.get(
            intake_id=intake_id,
            raise_exception_if_none=raise_exception_if_not_exists,
            show_deactivated=True,
        )
        if intake is not None:
            delete(intake).where(Intake.id == intake_id)
        return True


async def get_intake_crud(
    session: AsyncSession = Depends(get_async_session),
) -> IntakeCRUD:
    yield IntakeCRUD(session=session)


get_intakes_crud_context = contextlib.asynccontextmanager(get_intake_crud)
