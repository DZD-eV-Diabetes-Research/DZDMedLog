from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
import enum
from pydantic import validate_email, field_validator, model_validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.event.model import Event
from medlogserver.db.interview.model import Interview
from medlogserver.db.intake.model import Intake, IntakeCreate, IntakeUpdate
from medlogserver.db._base_crud import CRUDBase
from medlogserver.api.paginator import PageParams

log = get_logger()
config = Config()


class IntakeCRUD(CRUDBase[Intake, Intake, IntakeCreate, IntakeUpdate]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        filter_by_event_id: str = None,
        filter_by_interview_id: str = None,
        filter_by_proband_external_id: str = None,
        filter_by_study_id: str = None,
        pagination: PageParams = None,
    ) -> Sequence[Intake]:
        query = select(Intake)
        # prepare joins
        if filter_by_study_id:
            query = query.join(Interview).join(Event)
        elif filter_by_event_id or filter_by_proband_external_id:
            query = query.join(Interview)
        # prepare where filters
        if filter_by_study_id:
            query = query.where(Event.study_id == filter_by_study_id)
        if filter_by_event_id:
            query = query.where(Interview.event_id == filter_by_event_id)
        if filter_by_proband_external_id:
            query = query.where(
                Interview.proband_external_id == filter_by_proband_external_id
            )
        if filter_by_interview_id:
            query = query.where(Intake.interview_id == filter_by_interview_id)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def list_last_completed_interview_intakes_by_proband(
        self,
        study_id: str | uuid.UUID,
        proband_external_id: str,
        raise_exception_if_no_last_interview: Exception = None,
        pagination: PageParams = None,
    ) -> List[Intake]:

        last_interview_query = (
            select(Interview)
            .join(Event)
            .where(
                Interview.proband_external_id == proband_external_id
                and Event.study_id == study_id
            )
            .order_by(desc(Interview.interview_end_time_utc))
            .limit(1)
        )
        last_interview_results = await self.session.exec(statement=last_interview_query)
        last_interview: Interview = last_interview_results.one_or_none()

        if last_interview is None:
            if raise_exception_if_no_last_interview:
                raise raise_exception_if_no_last_interview
            return []

        query = (
            select(Intake)
            .where(Intake.interview_id == last_interview.id)
            .order_by(Intake.created_at)
        )
        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        intakes: Sequence[Intake] = results.all
        return intakes

    async def get(
        self,
        intake_id: str | UUID,
        study_id: str | UUID = None,
        raise_exception_if_none: Exception = None,
    ) -> Optional[Intake]:
        """_summary_

        Args:
            intake_id (str | UUID): _description_
            study_id (str | UUID, optional): Study id can be provied optional for some extra security on cost of perfomance. This way we check if the intake is part of the study. Defaults to None.
            raise_exception_if_none (Exception, optional): _description_. Defaults to None.

        Raises:
            raise_exception_if_none: _description_

        Returns:
            Optional[Intake]: _description_
        """
        query = select(Intake)
        if study_id:
            # caller provided a study id to double check if Interview runs under this study.
            query = query.join(Interview).join(Event).where(Event.study_id == study_id)
        query = query.where(Intake.id == intake_id)
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
        if type(intake) == IntakeCreate:
            intake = Intake(**intake.model_dump)
        self.session.add(intake)
        await self.session.commit()
        await self.session.refresh(intake)
        return intake
