from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Dict,
    TYPE_CHECKING,
    Any,
    Self,
)
import enum
from pydantic import (
    ValidationError,
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

from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugAPIRead,
    CustomDrugAPIRead,
)

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import (
    MedLogBaseModel,
    BaseTable,
    TimestampModel,
)


log = get_logger()
config = Config()


# AdministeredByDoctorAnswers = enum.Enum(
#    "AdministeredByDoctorAnswers", config.APP_CONFIG_PRESCRIBED_BY_DOC_ANSWERS
# )


class IntakeValidationError(ValueError):
    pass


class AdministeredByDoctorAnswers(str, enum.Enum):
    PRESCRIBED = "prescribed"
    RECOMMENDED = "recommended"
    NO = "no"
    UNKNOWN = "unknown"


class IntakeRegularOrAsNeededAnswers(str, enum.Enum):
    REGULAR = "regular"
    ASNEEDED = "as needed"


class IntervalOfDailyDoseAnswers(str, enum.Enum):
    UNKNOWN = "Unknown"
    DAILY = "Daily"
    EVERY_SECOND_DAY = "every 2. day"
    EVERY_THIRD_DAY = "every 3. day"
    EVERY_FOURTH_DAY = "every 4. day / twice a week"
    ONE_WEEK_OR_MORE = "intervals of one week or more"
    ONE_MONTH_OR_MORE = "intervals of one month or more"
    ONE_YEAR_OR_MORE = "intervals of one year or more"


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


class IntakeStartDateOption(str, enum.Enum):
    UNKNOWN = "unknown"
    AT_LEAST_12_MONTHS = "at_least_12_months"


class IntakeEndDateOption(str, enum.Enum):
    UNKNOWN = "unknown"
    ONGOING = "ongoing"


class IntakeUpdate(MedLogBaseModel, table=False):
    """
    Update an existing medication intake record.

    **Start Date** — exactly one of `intake_start_date` or `intake_start_date_option` must be set.
    Sending both returns 400. The omitted field is automatically nulled out.

    **End Date** — at most one of `intake_end_date` or `intake_end_date_option` may be set.
    Sending both returns 400. If neither is provided, `intake_end_date_option` defaults to `ONGOING`.
    The omitted field is automatically nulled out.

    **Intake mode** — mutually exclusive fields depending on `intake_regular_or_as_needed`:
    - `REGULAR`: `as_needed_dose_unit` must be `null`
    - `AS_NEEDED`: `regular_intervall_of_daily_dose` must be `null`
    """

    source_of_drug_information: Optional[SourceOfDrugInformationAnwers] = Field(
        default=None,
        description="How the drug/medication was identified (e.g. by name, active ingredient, barcode).",
    )
    is_activeingredient_equivalent_choice: bool = Field(
        default=False,
        description=(
            "Set to `true` when the searched drug was not found but an alternative with the same "
            "active ingredient was intentionally selected as a substitute. Defaults to `false`."
        ),
    )

    intake_start_date: Optional[date] = Field(
        default=None,
        description=(
            "Exact start date of the intake. "
            "Mutually exclusive with `intake_start_date_option` — exactly one of the two must be set. "
            "If this field is provided, `intake_start_date_option` is automatically set to `null`."
        ),
    )
    intake_start_date_option: Optional[IntakeStartDateOption] = Field(
        default=None,
        description=(
            "Use when no exact start date is available (e.g. `UNKNOWN`, `SINCE_BIRTH`). "
            "Mutually exclusive with `intake_start_date` — exactly one of the two must be set. "
            "If this field is provided, `intake_start_date` is automatically set to `null`."
        ),
    )

    intake_end_date: Optional[date] = Field(
        default=None,
        description=(
            "Exact end date of the intake. "
            "Mutually exclusive with `intake_end_date_option` — at most one of the two may be set. "
            "If this field is provided, `intake_end_date_option` is automatically set to `null`. "
            "If neither this nor `intake_end_date_option` is provided, `intake_end_date_option` defaults to `ONGOING`."
        ),
    )
    intake_end_date_option: Optional[IntakeEndDateOption] = Field(
        default=None,
        description=(
            "Use when no exact end date is available (e.g. `ONGOING`, `UNKNOWN`). "
            "Mutually exclusive with `intake_end_date` — at most one of the two may be set. "
            "If this field is provided, `intake_end_date` is automatically set to `null`. "
            "If neither this nor `intake_end_date` is provided, this field defaults to `ONGOING`."
        ),
    )

    administered_by_doctor: Optional[AdministeredByDoctorAnswers] = Field(
        default=None,
        description="Indicates whether the medication was administered by a doctor.",
    )
    intake_regular_or_as_needed: Optional[IntakeRegularOrAsNeededAnswers] = Field(
        default=None,
        description=(
            "Defines whether the medication is taken on a regular schedule or as needed. "
            "Drives mutual exclusivity of dose fields: "
            "`REGULAR` requires `regular_intervall_of_daily_dose` to be set and `as_needed_dose_unit` to be `null`. "
            "`AS_NEEDED` requires `as_needed_dose_unit` to be set and `regular_intervall_of_daily_dose` to be `null`."
        ),
    )
    dose_per_day: Optional[int] = Field(
        default=None,
        description="Number of doses taken per day.",
    )
    regular_intervall_of_daily_dose: Optional[IntervalOfDailyDoseAnswers] = Field(
        default=None,
        description=(
            "Interval between doses for regular intake. "
            "Required when `intake_regular_or_as_needed` is `REGULAR`. "
            "Must be `null` when `intake_regular_or_as_needed` is `AS_NEEDED`."
        ),
    )
    as_needed_dose_unit: Optional[int] = Field(
        default=None,
        description=(
            "Dose unit for as-needed intake. "
            "Required when `intake_regular_or_as_needed` is `AS_NEEDED`. "
            "Must be `null` when `intake_regular_or_as_needed` is `REGULAR`."
        ),
    )
    consumed_meds_today: Optional[ConsumedMedsTodayAnswers] = Field(
        default=None,
        description="Indicates whether the patient has already taken this medication today.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_start_date(
        cls, values: Dict[str, Any] | Self
    ) -> Dict[str, Any] | Self:
        if isinstance(values, dict):
            if (
                "intake_start_date" not in values
                and "intake_start_date_option" not in values
            ):
                return values  # neither sent, nothing to validate
            has_date: bool = values.get("intake_start_date") is not None
            has_option: bool = values.get("intake_start_date_option") is not None
        else:
            if (
                "intake_start_date" not in values.model_fields_set
                and "intake_start_date_option" not in values.model_fields_set
            ):
                return values
            has_date = getattr(values, "intake_start_date", None) is not None
            has_option = getattr(values, "intake_start_date_option", None) is not None

        if has_date and has_option:
            raise IntakeValidationError(
                "Only one of 'intake_start_date' or 'intake_start_date_option' may be set."
            )
        if not has_date and not has_option:
            raise IntakeValidationError(
                "Exactly one of 'intake_start_date' or 'intake_start_date_option' must be set."
            )

        if isinstance(values, dict):
            if has_date:
                values["intake_start_date_option"] = None
            else:
                values["intake_start_date"] = None
        else:
            if has_date:
                object.__setattr__(values, "intake_start_date_option", None)
            else:
                object.__setattr__(values, "intake_start_date", None)

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_end_date(cls, values: dict[str, Any] | Self) -> dict[str, Any] | Self:
        if isinstance(values, dict):
            if (
                "intake_end_date" not in values
                and "intake_end_date_option" not in values
            ):
                return values  # neither sent, nothing to validate
            has_date: bool = values.get("intake_end_date") is not None
            has_option: bool = values.get("intake_end_date_option") is not None
        else:
            if (
                "intake_end_date" not in values.model_fields_set
                and "intake_end_date_option" not in values.model_fields_set
            ):
                return values
            has_date = getattr(values, "intake_end_date", None) is not None
            has_option = getattr(values, "intake_end_date_option", None) is not None

        if has_date and has_option:
            raise IntakeValidationError(
                "Only one of 'intake_end_date' or 'intake_end_date_option' may be set."
            )

        if isinstance(values, dict):
            if not has_date and not has_option:
                values["intake_end_date_option"] = IntakeEndDateOption.ONGOING
            elif has_date:
                values["intake_end_date_option"] = None
            else:
                values["intake_end_date"] = None
        else:
            if not has_date and not has_option:
                object.__setattr__(
                    values, "intake_end_date_option", IntakeEndDateOption.ONGOING
                )
            elif has_date:
                object.__setattr__(values, "intake_end_date_option", None)
            else:
                object.__setattr__(values, "intake_end_date", None)

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_intake_regular_or_as_needed(
        cls, values: Dict[str, Any] | Self
    ) -> Dict[str, Any] | Self:
        if isinstance(values, dict):
            intake_mode = values.get("intake_regular_or_as_needed")
        else:
            intake_mode = getattr(values, "intake_regular_or_as_needed", None)

        if intake_mode == IntakeRegularOrAsNeededAnswers.REGULAR:
            if isinstance(values, dict):
                if values.get("as_needed_dose_unit") is not None:
                    raise IntakeValidationError(
                        "When choosing regular intake, as_needed_dose_unit must be empty"
                    )
            else:
                if getattr(values, "as_needed_dose_unit", None) is not None:
                    raise IntakeValidationError(
                        "When choosing regular intake, as_needed_dose_unit must be empty"
                    )
        elif intake_mode == IntakeRegularOrAsNeededAnswers.ASNEEDED:
            if isinstance(values, dict):
                if values.get("regular_intervall_of_daily_dose") is not None:
                    raise IntakeValidationError(
                        "When choosing 'as needed' intake, regular_intervall_of_daily_dose must be empty"
                    )
            else:
                if getattr(values, "regular_intervall_of_daily_dose", None) is not None:
                    raise IntakeValidationError(
                        "When choosing 'as needed' intake, regular_intervall_of_daily_dose must be empty"
                    )

        return values


class IntakeCreateAPI(IntakeUpdate, table=False):
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

    consumed_meds_today: ConsumedMedsTodayAnswers = Field()


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
    drug: DrugAPIRead | CustomDrugAPIRead
