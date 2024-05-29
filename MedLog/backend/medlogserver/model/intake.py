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


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable


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


class IntakeCreateAPI(MedLogBaseModel, table=False):
    """This class/table also saves some extra question for every interview. This is 1-to-1 what the old IDOM software did. and its a mess.
    i fucking hate it. its unflexible, complex and ugly!
    for a future version we need an extra class/table to store extra question on a per study base.
    fields (with meatdata like options) could be defined in json schema. so clients can generate dynamic forms relatively easy.
    """

    pharmazentralnummer: Annotated[
        Optional[str],
        StringConstraints(
            strip_whitespace=True,
            to_upper=True,
            pattern=r"^(PZN-)|(-)|( -)?\d{2,9}$",
            max_length=12,
            min_length=2,
        ),
    ] = Field(
        description="Take the Pharmazentralnummer in many formats, but all formats will be normalized to just a 8 digit number.",
        default=None,
        schema_extra={"examples": ["23894732", "PZN-88888888"]},
    )
    custom_drug_id: Optional[uuid.UUID] = Field(
        description="Alternative to pharmazentralnummer. If a drug is not findable in the Arzeimittelindex, and the pharmazentralnummer(pzn) is unknown, the id of a custom drug can be provided.",
        default=None,
        schema_extra={
            "examples": [
                "ab1b8b63-cc1f-4ac0-8d0d-5dffad322e0c",
                "231583a9-95bf-4876-8b41-3c77ff396101",
            ]
        },
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
    def clean_pzn(self):
        # todo:
        return self
        self["pharmazentralnummer"] = (
            self.pharmazentralnummer.replace("PZN", "")
            .replace("-", "")
            .replace(" ", "")
        )
        self.pharmazentralnummer = self.pharmazentralnummer.rjust(8, 0)

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

    @model_validator(mode="after")
    def either_set_pzn_or_custom_drug(self):
        if not self.pharmazentralnummer and not self.custom_drug_id:
            raise ValueError(
                "Can not create intake record. Either `pharmazentralnummer` or `custom_drug_id` must be set. Both are empty atm."
            )
        if self.pharmazentralnummer and self.custom_drug_id:
            raise ValueError(
                "Can not create intake record. Either `pharmazentralnummer` or `custom_drug_id` must be set. Both are set atm."
            )
        return self


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


class IntakeUpdate(IntakeCreateAPI, table=False):
    pass


class Intake(IntakeCreate, BaseTable, table=True):
    __tablename__ = "intake"
    pharmazentralnummer: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=8,
            min_length=2,
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
