from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, StringConstraints
from fastapi import Depends
from typing import Optional
from sqlmodel import Field
from datetime import datetime
import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel

log = get_logger()
config = Config()


class DrugUpdaterStatus(MedLogBaseModel):
    update_available: bool = Field(
        description="Is a new dataset for the drug database available"
    )
    update_available_version: Optional[str] = Field(
        description="If update available this show the version string"
    )
    update_running: bool = Field(
        description="Is an update of the drug database currently running"
    )
    last_update_run_datetime_utc: Optional[datetime] = Field(
        description="When did the last drug database update end."
    )
    last_update_run_error: Optional[str] = Field(
        description="If the last update failed, this is the error message"
    )
    current_drug_data_version: Optional[str] = Field(
        description="The version string of the current drug db dataset."
    )
    current_drug_data_ready_to_use: bool = Field(
        description="The version string of the current drug db dataset."
    )
