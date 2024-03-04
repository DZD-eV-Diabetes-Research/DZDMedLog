from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel

import uuid
from uuid import UUID

from medlogserver.db._session import get_async_session, get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseModel, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.normpackungsgroessen import (
    Normpackungsgroessen,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import DrugCRUDBase
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()

from sqlmodel import func


class NormpackungsgroessenCRUD(
    DrugCRUDBase[
        Normpackungsgroessen,
        Normpackungsgroessen,
        Normpackungsgroessen,
        Normpackungsgroessen,
    ]
):
    pass
