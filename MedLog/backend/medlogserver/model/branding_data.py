from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from fastapi import Depends
from typing import Optional
from sqlmodel import Field

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel

log = get_logger()
config = Config()


class BrandingData(MedLogBaseModel):
    support_email: Optional[str] = Field(
        default=None, description="The email address for user suport"
    )
