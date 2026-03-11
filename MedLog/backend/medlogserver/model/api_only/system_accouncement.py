from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import validate_email, validator, StringConstraints
from fastapi import Depends
from typing import Optional
from sqlmodel import Field

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseApiModel

log = get_logger()
config = Config()


class SystemAnnouncement(MedLogBaseApiModel):
    id: str = Field(
        description="A unique has for each message. This id can used by the client to e.g. manage 'user has seen it' states"
    )
    type: Literal["info", "warning", "alert"]
    message: str
