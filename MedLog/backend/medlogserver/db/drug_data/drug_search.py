from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, func, col
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID
import shlex

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import Drug
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS

log = get_logger()
config = Config()


class DrugCRUD(
    create_crud_base(
        table_model=Drug,
        read_model=Drug,
        create_model=Drug,
        update_model=Drug,
    )
):

    async def search(
        self,
        search_term: str,
        pagination: QueryParamsInterface = None,
        **kwargs_ref_fields
    ) -> Sequence[Drug]:
        # normalize quotes
        search_term = (
            search_term.replace("'", '"')
            .replace("`", '"')
            .replace("´", '"')
            .replace("„", '"')
            .replace("“", '"')
            .replace("‘", '"')
        )
        # split search term into tokens (single words or multiple words enclosed by quotes)
        search_term_tokens = shlex.split(search_term)
        # remove tokens that are too short. we will ignore these
        search_term_tokens = [token for token in search_term_tokens if len(token) > 2]

        select(Drug).where()
