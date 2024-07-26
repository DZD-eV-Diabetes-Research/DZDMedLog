from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, col, func

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable
from medlogserver.model.worker_job import (
    WorkerJob,
    WorkerJobCreate,
    WorkerJobUpdate,
    WorkerJobState,
)
from medlogserver.db._base_crud import create_crud_base
from medlogserver.api.paginator import QueryParamsInterface

log = get_logger()
config = Config()


class WorkerJobCRUD(
    create_crud_base(
        table_model=WorkerJob,
        read_model=WorkerJob,
        create_model=WorkerJobCreate,
        update_model=WorkerJobUpdate,
    )
):

    async def list(
        self,
        filter_user_id: Optional[UUID] = None,
        filter_job_state: Optional[WorkerJobState] = None,
        filter_tags: Optional[List[str]] = None,
        filter_intervalled_job: Optional[bool] = None,
        hide_user_jobs: bool = False,
        pagination: QueryParamsInterface = None,
    ) -> Sequence[WorkerJob]:
        if filter_tags is None:
            filter_tags = []
        if isinstance(filter_user_id, str):
            filter_user_id: UUID = UUID(filter_user_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(WorkerJob)
        if filter_user_id:
            # query = query.where(Event.study_id == prep_uuid_for_qry(filter_study_id))
            query = query.where(WorkerJob.user_id == filter_user_id)
        if filter_job_state:
            query = query.where(WorkerJob.state == filter_job_state)
        if hide_user_jobs:
            query = query.where(WorkerJob.user_id is None)
        for f_tag in filter_tags:
            query = query.filter(col(WorkerJob.tags).contains(f_tag))
        if pagination:
            query = pagination.append_to_query(query)
        if filter_intervalled_job is not None:
            if filter_intervalled_job == True:
                query = query.where(WorkerJob.interval_params != None)
            elif filter_intervalled_job == False:
                query = query.where(WorkerJob.interval_params == None)

        print("list_job_query", query)

        # log.debug(f"List Event query: {query}")
        results = await self.session.exec(statement=query)
        return results.all()

    async def count(
        self,
        filter_user_id: Optional[UUID] = None,
        filter_job_state: Optional[WorkerJobState] = None,
        filter_tags: Optional[List[str]] = None,
        hide_user_jobs: bool = False,
    ) -> Sequence[WorkerJob]:
        if isinstance(filter_user_id, str):
            filter_user_id: UUID = UUID(filter_user_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(func.count()).select_from(WorkerJob)
        if filter_user_id:
            # query = query.where(Event.study_id == prep_uuid_for_qry(filter_study_id))
            query = query.where(WorkerJob.user_id == filter_user_id)
        if filter_job_state:
            query = query.where(WorkerJob.state == filter_job_state)
        if hide_user_jobs:
            query = query.where(WorkerJob.user_id is None)
        for f_tag in filter_tags:
            query = query.filter(col(WorkerJob.tags).contains(f_tag))
        # log.debug(f"List Event query: {query}")
        results = await self.session.exec(statement=query)
        return results.first()
