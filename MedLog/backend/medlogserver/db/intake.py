from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
import enum
from pydantic import validate_email, field_validator, model_validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends, HTTPException, status
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc, and_

from datetime import datetime, timezone
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
from medlogserver.model.event import Event
from medlogserver.model.interview import Interview
from medlogserver.model.intake import (
    Intake,
    IntakeCreate,
    IntakeUpdate,
    IntakeDetailListItem,
)
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugAPIRead,
    drug_to_drugAPI_obj,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class IntakeCRUD(
    create_crud_base(
        table_model=Intake,
        read_model=Intake,
        create_model=IntakeCreate,
        update_model=IntakeUpdate,
    )
):
    async def list(
        self,
        filter_event_id: str = None,
        filter_interview_id: str = None,
        filter_proband_external_id: str = None,
        filter_study_id: str = None,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[Intake]:
        query = select(Intake).distinct()
        # prepare joins
        if filter_study_id:
            query = query.join(Interview).join(Event)
        elif filter_event_id or filter_proband_external_id:
            query = query.join(Interview)
        # prepare where filters
        if filter_study_id:
            query = query.where(Event.study_id == filter_study_id)
        if filter_event_id:
            query = query.where(Interview.event_id == filter_event_id)
        if filter_proband_external_id:
            query = query.where(
                Interview.proband_external_id == filter_proband_external_id
            )
        if filter_interview_id:
            query = query.where(Intake.interview_id == filter_interview_id)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def count(
        self,
        filter_event_id: str = None,
        filter_interview_id: str = None,
        filter_proband_external_id: str = None,
        filter_study_id: str = None,
    ) -> int:
        # Todo that is stupid. we need a batter way to return total count for pagination, then repeat the query.
        return len(
            await self.list(
                filter_event_id=filter_event_id,
                filter_interview_id=filter_interview_id,
                filter_proband_external_id=filter_proband_external_id,
                filter_study_id=filter_study_id,
            )
        )

    async def list_detailed(
        self,
        filter_event_id: str = None,
        filter_interview_id: str = None,
        filter_proband_external_id: str = None,
        filter_study_id: str = None,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[IntakeDetailListItem]:
        query = select(Intake, Interview, Event).select_from(Intake)
        query = query.join(Interview).join(Event)
        # prepare where filters
        if filter_study_id:
            query = query.where(Event.study_id == filter_study_id)
        if filter_event_id:
            query = query.where(Interview.event_id == filter_event_id)
        if filter_proband_external_id:
            query = query.where(
                Interview.proband_external_id == filter_proband_external_id
            )
        if filter_interview_id:
            query = query.where(Intake.interview_id == filter_interview_id)
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        detailed_intakes: List[IntakeDetailListItem] = []
        for intake, interview, event in results:
            drug_read: DrugAPIRead = None
            drug_result = await self.session.exec(
                select(DrugData).where(DrugData.id == intake.drug_id)
            )
            drug = drug_result.one()
            drug_read = await drug_to_drugAPI_obj(drug)
            detailed_intakes.append(
                IntakeDetailListItem(
                    **intake.model_dump(),
                    event=event,
                    interview=interview,
                    drug=drug_read,
                )
            )

        return detailed_intakes

    async def list_last_completed_interview_intakes_by_proband(
        self,
        study_id: str | uuid.UUID,
        proband_external_id: str,
        raise_exception_if_no_last_interview: Exception = None,
        pagination: QueryParamsInterface = None,
    ) -> List[Intake]:

        last_interview_query = (
            select(Interview)
            .join(Event)
            .where(
                and_(
                    Interview.proband_external_id == proband_external_id,
                    Event.study_id == study_id,
                )
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
        intakes: Sequence[Intake] = results.all()
        return intakes

    async def get(
        self,
        id_: str | UUID,
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
        query = query.where(Intake.id == id_)
        results = await self.session.exec(statement=query)
        intake: Intake | None = results.one_or_none()
        if intake is None and raise_exception_if_none:
            raise raise_exception_if_none
        return intake

    async def assert_belongs_to_study(
        self,
        intake_id: UUID,
        study_id: UUID,
        interview_id: UUID = None,
        raise_exception_if_not=None,
    ) -> bool:
        query = (
            select(Intake)
            .join(Interview)
            .join(Event)
            .where(and_(Event.study_id == study_id, Intake.id == intake_id))
        )
        if interview_id is not None:
            query = query.where(Interview.id == interview_id)
        log.debug(f"##query: {query}")
        results = await self.session.exec(statement=query)

        intake: Event | None = results.first()
        log.debug(f"##query: {query} \nRESULT: {intake}")
        if intake is None:
            if raise_exception_if_not:
                raise raise_exception_if_not
            return False
        return True
