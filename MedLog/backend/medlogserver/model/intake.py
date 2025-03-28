from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
import enum
from pydantic import (
    validate_email,
    field_validator,
    model_validator,
    StringConstraints,
    ValidationInfo,
)
from fastapi import Depends
from typing import Optional
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, desc
from datetime import datetime, timezone, date
import uuid
from uuid import UUID
from medlogserver.model.event import Event
from medlogserver.model.interview import Interview
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugAPIRead,
)

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import (
    MedLogBaseModel,
    BaseTable,
    ExportBaseModel,
    TimestampModel,
)


log = get_logger()
config = Config()


# AdministeredByDoctorAnswers = enum.Enum(
#    "AdministeredByDoctorAnswers", config.APP_CONFIG_PRESCRIBED_BY_DOC_ANSWERS
# )


class AdministeredByDoctorAnswers(str, enum.Enum):
    PRESCRIBED = "prescribed"
    RECOMMENDED = "recommended"
    NO = "no"
    UNKNOWN = "unknown"


class IntakeRegularOrAsNeededAnswers(str, enum.Enum):
    REGULAR = "regular"
    ASNEEDED = "as needed"


class IntervalOfDailyDoseAnswers(str, enum.Enum):
    UNKNOWN = "Unkown"
    DAILY = "Daily"
    EVERY_SECOND_DAY = "every 2. day"
    EVERY_THIRD_DAY = "every 3. day"
    EVERY_FOURTH_DAY = "every 4. day / twice a week"
    ONE_WEEK_OR_MORE = "intervals of one week or more"


class ConsumedMedsTodayAnswers(str, enum.Enum):
    YES = "Yes"
    NO = "No"
    UNKNOWN = "UNKNOWN"


class SourceOfDrugInformationAnwers(str, enum.Enum):
    DRUG_PACK_SCANNED_PZN = "Medication package: Scanned PZN"
    DRUG_PACK_TYPED_PZN = "Medication package: Typed in PZN"
    DRUG_PACK_NAME = "Medication package: Drug name"
    DRUG_LEAFLET = "Medication leaflet"
    MEDICATION_PLAN = "Study participant: medication plan"
    PRESCRIPTION = "Study participant: Medication prescription"
    PARTICIPANT_SPECIFICATION = "Study participant: verbal specification"
    FOLLOW_UP_PZN = "Follow up via phone/message: Typed in PZN"
    FOLLOW_UP_DRUG_NAME = "Follow up via phone/message: Medication name"


class IntakeCreateAPI(MedLogBaseModel, table=False):
    """This class/table also saves some extra question for every interview. This is 1-to-1 what the old IDOM software did. and its a mess.
    i fucking hate it. its unflexible, complex and ugly!
    for a future version we need an extra class/table to store extra question on a per study base.
    fields (with meatdata like options) could be defined in json schema. so clients can generate dynamic forms relatively easy.
    """

    drug_id: uuid.UUID = Field(
        description="ID of the drug as returned from the drug search.",
        default=None,
        foreign_key="drug.id",
    )
    source_of_drug_information: Optional[SourceOfDrugInformationAnwers] = Field(
        default=None,
        description="How was the drug/medication identified.",
    )
    intake_start_time_utc: date = Field()
    intake_end_time_utc: Optional[date] = Field(default=None)
    administered_by_doctor: Optional[AdministeredByDoctorAnswers] = Field(default=None)
    intake_regular_or_as_needed: Optional[IntakeRegularOrAsNeededAnswers] = Field(
        default=None,
        description="If a med is taken regualr or as needed. When choosen regular the field `regular_intervall_of_daily_dose` is mandatory and `as_needed_dose_unit` must be `None`/`null`. When the choosen `as needed` the oposite is true. This is the old IDOM behaviour, its ugly, i hate it and it will change in a futue version",
    )
    dose_per_day: Optional[int] = Field(default=None)
    regular_intervall_of_daily_dose: Optional[IntervalOfDailyDoseAnswers] = Field(
        default=None
    )
    as_needed_dose_unit: Optional[int] = Field()
    consumed_meds_today: ConsumedMedsTodayAnswers = Field()

    @model_validator(mode="after")
    def validate_intake_regular_or_as_needed(self):
        if self.intake_regular_or_as_needed == IntakeRegularOrAsNeededAnswers.REGULAR:
            if self.as_needed_dose_unit is not None:
                raise ValueError(
                    "When choosing regular intake, as_needed_dose_unit must be empty"
                )
        elif (
            self.intake_regular_or_as_needed == IntakeRegularOrAsNeededAnswers.ASNEEDED
        ):
            if self.regular_intervall_of_daily_dose is not None:
                raise ValueError(
                    "When choosing 'as needed' intake, regular_intervall_of_daily_dose must be empty"
                )
        return self


class IntakeUpdate(IntakeCreateAPI, table=False):
    pass


class IntakeCreate(IntakeCreateAPI, table=False):
    """This class/table also saves some extra question for every interview. This is 1-to-1 what the old IDOM software did. and its a mess.
    i fucking hate it. its unflexible, complex and ugly!
    for a future version we need an extra class/table to store extra question on a per study base.
    fields (with meatdata like options) could be defined in json schema. so clients can generate dynamic forms relatively easy.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    interview_id: uuid.UUID = Field(foreign_key="interview.id")

    @field_validator("interview_id")
    @classmethod
    def foreign_key_to_uuid(cls, v: str | uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        return MedLogBaseModel.id_to_uuid(v, info)


class Intake(IntakeCreate, BaseTable, TimestampModel, table=True):
    __tablename__ = "intake"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class IntakeExport(IntakeCreate, BaseTable, table=False):
    created_at: datetime = Field(exclude=True)
    interview_id: UUID = Field(exclude=True)
    id: uuid.UUID = Field()


class IntakeDetailListItem(IntakeCreate, BaseTable, table=False):
    interview: Interview
    event: Event
    drug: DrugAPIRead
