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
from medlogserver.db.base import MedLogBaseModel, BaseTable
from medlogserver.db.wido_gkv_arzneimittelindex.model.ergaenzung_amtlich import (
    ATCErgaenzungAmtlich,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import create_drug_crud_base

log = get_logger()
config = Config()


class ATCErgaenzungAmtlichCRUD(
    create_drug_crud_base(
        table_model=ATCErgaenzungAmtlich,
        read_model=ATCErgaenzungAmtlich,
        create_model=ATCErgaenzungAmtlich,
        update_model=ATCErgaenzungAmtlich,
    )
):
    pass
