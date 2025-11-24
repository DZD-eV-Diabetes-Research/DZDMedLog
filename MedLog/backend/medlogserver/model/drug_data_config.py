from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
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


class DrugDataConfig(MedLogBaseModel):
    drug_data_source_name: str = Field(
        default=None, description="The name of the durg data source"
    )
    drug_data_source_info_url: Optional[str] = Field(
        default=None,
        description="An external url with information about the drug data source.",
    )
    supports_force_manual_update: bool = Field(
        description="Can the endpoint PUT-`/api/drug/db/update` be used to force the drug data model to download the most recent drug data from the external source."
    )
    supports_scheduled_auto_update: bool = Field(
        description="Will the drug data be automaticly updated in the background from the external source."
    )
