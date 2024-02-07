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
from medlogserver.db.base import Base, BaseTable
from medlogserver.db.event.event import Event
from medlogserver.db.interview.interview import Interview

# TODO: this generated a circular import we need to seperate model and crud classes
# from medlogserver.db.intake_auth import IntakeAuthRefreshTokenCRUD


log = get_logger()
config = Config()

AdministeredByDoctorAnswers = enum.Enum(
    "AdministeredByDoctorAnswers", config.APP_CONFIG_PRESCRIBED_BY_DOC_ANSWERS
)


class IntakeRegularOrAsNeededAnswers(str, enum.Enum):
    REGULAR = "regular"
    ASNEEDED = "as needed"


class IntervalOfDailyDoseAnswers(str, enum.Enum):
    UNKNOWN = "regular"
    DAILY = "as needed"
    EVERY_SECOND_DAY = "every 2. day"
    EVERY_THIRD_DAY = "every 3. day"
    EVERY_FOURTH_DAY = "every 4. day / twice a week"
    ONE_WEEK_OR_MORE = "intervals of one week or more"


class ConsumedMedsTodayAnswers(str, enum.Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "UNKNOWN"


class IntakeCreate(Base, table=False):
    """This class/table also saves some extra question for every interview. This is 1-to-1 what the old IDOM software did. and its a mess.
    i fucking hate it. its unflexible, complex and ugly!
    for a future version we need an extra class/table to store extra question on a per study base.
    fields (with meatdata like options) could be defined in json schema. so clients can generate dynamic forms relatively easy.
    """

    interview_id: Optional[str | uuid.UUID] = Field()
    pharmazentralnummer: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            to_upper=True,
            pattern=r"^(PZN-)|(-)|( -)?\d{8,9}$",
            max_length=12,
            min_length=8,
        ),
    ] = Field(
        description="Take the Pharmazentralnummer in many formats, but all formats will be normalized to just a 8 digit number.",
        schema_extra={"examples": ["23894732", "PZN-88888888"]},
    )
    intake_start_time_utc: datetime = Field()
    intake_end_time_utc: datetime = Field(default=None)
    administered_by_doctor: Optional[AdministeredByDoctorAnswers] = Field(default=None)
    intake_regular_or_as_needed: Optional[IntakeRegularOrAsNeededAnswers] = Field(
        default=None,
        description="If a med is taken regualr or as needed. When choosen regular the field `regular_intervall_of_daily_dose` is mandatory and `as_needed_dose_unit` must be `None`/`null`. When the choosen `as needed` the oposite is true. This is the old IDOM behaviour, its ugly, i hate it and it will change in a futue version",
    )
    dose_per_day: Optional[int] = Field(default=None)
    regular_intervall_of_daily_dose: Optional[IntervalOfDailyDoseAnswers] = Field(
        default=None
    )
    as_needed_dose_unit: int
    consumed_meds_today: ConsumedMedsTodayAnswers = Field()

    @model_validator(mode="after")
    def clean_pzn(self, values):
        values["pharmazentralnummer"]: str = (
            values["pharmazentralnummer"]
            .replace("PZN", "")
            .replace("-", "")
            .replace(" ", "")
        )

    @field_validator("intake_regular_or_as_needed")
    def validate_intake_regular_or_as_needed(cls, value, values):
        if (
            values["intake_regular_or_as_needed"]
            == IntakeRegularOrAsNeededAnswers.REGULAR
        ):
            if values["as_needed_dose"] is not None:
                raise ValueError(
                    "When choosing regular intake, dose unit muste be empty"
                )
        elif (
            values["intake_regular_or_as_needed"]
            == IntakeRegularOrAsNeededAnswers.ASNEEDED
        ):
            if values["regular_intervall_of_daily_dose"] is not None:
                raise ValueError(
                    "When choosing 'as needed' intake, regular_intervall_of_daily_dose must be empty"
                )
        return values["intake_regular_or_as_needed"]


class IntakeUpdate(IntakeCreate, table=False):
    pass


class Intake(IntakeCreate, BaseTable, table=True):
    __tablename__ = "intake"
    interview_id: uuid.UUID = Field(foreign_key="interview.id")
    pharmazentralnummer: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=8,
            min_length=8,
        ),
    ] = Field(
        description="Pharmazentralnummer as 8 digits only",
        schema_extra={"examples": ["23894732"]},
    )

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
        filter_by_interview_id: str = None,
        filter_by_proband_external_id: str = None,
        filter_by_study_id: str = None,
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
        results = await self.session.exec(statement=query)
        return results.all()

    async def list_last_completed_interview_intakes_by_proband(
        self,
        study_id: str | uuid.UUID,
        proband_external_id: str,
        raise_exception_if_no_last_interview: Exception = None,
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
