from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
import enum
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel
import datetime
import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
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


class ProbandExternalIdNormalization(str, enum.Enum):
    """How a proband external ID is normalized before it is validated, stored and matched.

    Applied per study. Replaces the former global ``PROBAND_IDS_CASE_SENSETIVE`` flag.
    """

    NONE = "none"  # store/match exactly as entered (case-sensitive)
    UPPERCASE = "uppercase"  # fold to upper case (e.g. "aaa1111" -> "AAA1111")
    LOWERCASE = "lowercase"  # fold to lower case (e.g. "AAA1111" -> "aaa1111")


def normalize_proband_external_id(
    value: Optional[str],
    normalization: Optional["ProbandExternalIdNormalization"],
) -> Optional[str]:
    """Apply a study's proband-ID normalization rule to a raw value.

    Pure/side-effect free so it can be shared between the write path, the lookup
    path and the validation endpoint (single source of truth). ``None`` in -> ``None`` out.

    Leading/trailing whitespace is *always* stripped, independent of the case rule
    (including ``NONE``). This happens before validation, storage and matching so that a
    value like ``"AAA1111 "`` can never be stored-with-space and then silently fail to
    match later exact-value lookups.
    """
    if value is None:
        return None
    value = value.strip()
    if normalization == ProbandExternalIdNormalization.UPPERCASE:
        return value.upper()
    if normalization == ProbandExternalIdNormalization.LOWERCASE:
        return value.lower()
    return value


class StudyCreateAPI(MedLogBaseModel, table=False):
    display_name: Optional[str] = Field(
        default=None,
        index=True,
        max_length=128,
        unique=True,
        schema_extra={
            "examples": [
                "Prädiabetes-Lebensstil-Interventions-Studie (PLIS)",
                "BARIA-DDZ-Studie",
            ]
        },
    )
    no_permissions: bool = Field(
        default=config.APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT,
        description="If this is set to True all user have access as interviewers to the study. This can be utile when this MedLog instance only host one study. Admin access still need to be allocated explicit.",
    )
    proband_external_id_pattern: Optional[str] = Field(
        default=None,
        max_length=1024,
        description=(
            "Optional regular expression a proband external ID must fully match to be accepted "
            "for this study. If unset (default), any proband ID is accepted (status quo). "
            "The pattern is validated (compiled) when the study is saved."
        ),
        schema_extra={"examples": ["^[A-Z]{3}[0-9]{4}$"]},
    )
    proband_external_id_pattern_error_text: Optional[str] = Field(
        default=None,
        max_length=1024,
        description=(
            "Human-readable error text shown when a proband ID does not match "
            "'proband_external_id_pattern'. Should describe the expected format in plain "
            "language instead of exposing the raw regular expression. A generic fallback text "
            "is used when unset."
        ),
        schema_extra={"examples": ["Expected 3 uppercase letters followed by 4 digits, e.g. AAA1111"]},
    )
    proband_external_id_normalization: ProbandExternalIdNormalization = Field(
        default=ProbandExternalIdNormalization.NONE,
        description=(
            "How proband external IDs are normalized before validation, storage and matching "
            "for this study. Replaces the former global 'PROBAND_IDS_CASE_SENSETIVE' flag."
        ),
    )
    proband_external_id_example: Optional[str] = Field(
        default=None,
        max_length=1024,
        description=(
            "Optional positive example of a valid proband external ID for this study "
            "(e.g. 'AAA1111'), so the frontend can proactively show 'e.g. …' next to the "
            "input. Purely informational — it is not validated against the pattern."
        ),
        schema_extra={"examples": ["AAA1111"]},
    )


class StudyCloneAPI(MedLogBaseModel, table=False):
    """Request body for cloning the setup of an existing study into a new one.

    Only the name is provided by the caller. Everything else that makes up the *setup*
    of the source study (all :class:`StudyCreateAPI` fields, e.g. the proband-ID pattern)
    plus its event structure is copied by the backend. See ``POST /study/{study_id}/clone``.
    """

    display_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=128),
    ] = Field(
        description=(
            "Name of the new study. Must be unique across all studies, like any study name."
        ),
        schema_extra={"examples": ["BARIA-DDZ-Studie (Follow-Up)"]},
    )


class StudyUpdate(StudyCreateAPI):
    pass

    deactivated: bool = Field(default=False)


class StudyCreate(StudyUpdate):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)


class Study(StudyCreate, BaseTable, TimestampModel, table=True):
    __tablename__ = "study"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class StudyExport(StudyCreate, BaseTable, table=False):
    deactivated: bool = Field(exclude=True)
    no_permissions: bool = Field(exclude=True)
    created_at: datetime.datetime = Field(exclude=True)
