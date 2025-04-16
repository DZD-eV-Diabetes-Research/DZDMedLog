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


class AppVersion(MedLogBaseModel):
    version: str = Field(description="The version string of the application")
    branch: str = Field(description="The branch this version was build from")
