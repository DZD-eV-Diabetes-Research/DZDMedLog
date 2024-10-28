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
from getversion import get_module_version
import medlogserver
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.healthcheck import HealthCheck, HealthCheckReport
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.db.drug_data.drug_search.search_interface import (
    get_drug_search_context,
)
from medlogserver.db.drug_data.drug_dataset_version import (
    DrugDataSetVersionCRUD,
    DrugDataSetVersion,
)
from medlogserver.db._session import get_async_session_context

from medlogserver.db._base_crud import DatabaseInteractionBase

log = get_logger()
config = Config()


class HealthcheckRead(DatabaseInteractionBase):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
    ) -> HealthCheck:
        # basic db check
        query = select(1)
        results = await self.session.exec(statement=query)
        if results.first() == 1:
            return HealthCheck(healthy=True)
        return HealthCheck(healthy=False)

    async def get_report(
        self,
    ) -> HealthCheckReport:
        healthcheck = HealthCheckReport(
            name=config.APP_NAME,
            version=get_module_version(medlogserver)[0],
            db_working=False,
            drugs_imported=False,
            last_worker_run_succesfull=True,  # not yet implemented. always true
            drug_search_index_working=False,
        )
        # basic db check
        query = select(1)
        results = await self.session.exec(statement=query)
        if results.first() == 1:
            healthcheck.db_working = True
        # drugs imported?
        async with DrugDataSetVersionCRUD.crud_context(
            self.session
        ) as dataset_version_crud:
            dataset_version_crud: DrugDataSetVersionCRUD = dataset_version_crud
            dataset_version = await dataset_version_crud.get_current()
            if dataset_version and dataset_version.import_status == "done":
                healthcheck.drugs_imported = True
        # drug search check
        async with get_drug_search_context(self.session) as drug_search:
            healthcheck.drug_search_index_working = await drug_search.healthy()
        return healthcheck
