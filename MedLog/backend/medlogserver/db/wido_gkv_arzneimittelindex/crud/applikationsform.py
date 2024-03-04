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


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.wido_gkv_arzneimittelindex.model.applikationsform import (
    Applikationsform,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model.ai_data_version import (
    AiDataVersion,
)

from medlogserver.db.wido_gkv_arzneimittelindex.crud._base import (
    DrugCRUDBase,
    create_drug_crud_base,
)

log = get_logger()
config = Config()


class ApplikationsformCRUD(
    create_drug_crud_base(
        table_model=Applikationsform,
        read_model=Applikationsform,
        create_model=Applikationsform,
        update_model=Applikationsform,
    )
):
    pass
