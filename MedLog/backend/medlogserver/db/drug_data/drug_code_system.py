from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func, col, desc
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID
from sqlalchemy.orm import selectinload

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.drug_attr import DrugValRef
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem

log = get_logger()
config = Config()


class DrugCodeSystemCRUD(
    create_crud_base(
        table_model=DrugCodeSystem,
        read_model=DrugCodeSystem,
        create_model=DrugCodeSystem,
        update_model=DrugCodeSystem,
    )
):
    pass
