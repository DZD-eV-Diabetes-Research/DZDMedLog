from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Dict,
    Awaitable,
)
from pydantic import validate_email, StringConstraints, field_validator, model_validator
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Field, select, delete, Column, JSON, SQLModel, col, func
from sqlalchemy.sql.operators import is_, is_not, or_, and_

import uuid
from uuid import UUID

from medlogserver.config import Config
from medlogserver.log import get_logger

from medlogserver.model.worker_job import (
    WorkerJob,
    WorkerJobCreate,
    WorkerJobUpdate,
    WorkerJobState,
)
from medlogserver.worker.tasks import Tasks
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
        pagination: Optional[QueryParamsInterface] = None,
        filter_user_id: Optional[UUID] = None,
        filter_job_state: Optional[WorkerJobState] = None,
        filter_tags: Optional[List[str]] = None,
        filter_intervalled_job: Optional[bool] = None,
        filter_task: Optional[Tasks | str] = None,
        hide_user_jobs: bool = False,
    ) -> List[WorkerJob]:
        # log.debug(
        #    f"filter_user_id: {filter_user_id}\nfilter_job_state: {filter_job_state}\nfilter_tags: {filter_tags}\nfilter_intervalled_job: {filter_intervalled_job}\nhide_user_jobs: {hide_user_jobs}\n"
        # )
        if filter_tags is None:
            filter_tags = []
        if isinstance(filter_user_id, str):
            filter_user_id: UUID = UUID(filter_user_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(WorkerJob)
        if filter_user_id:
            query = query.where(WorkerJob.user_id == filter_user_id)
        if hide_user_jobs:
            query = query.where(is_(WorkerJob.user_id, None))
        if pagination:
            query = pagination.append_to_query(query)
        if filter_task:
            if isinstance(filter_task, Tasks):
                filter_task = filter_task.name
            query = query.where(WorkerJob.task_name == filter_task)
        results = await self.session.exec(statement=query)
        all_jobs = results.all()
        # json quering is very finicky on certain databases. lets do filtering on python side

        if filter_tags:
            all_jobs = [
                j for j in all_jobs if bool(set(filter_tags).issubset(set(j.tags)))
            ]

        if filter_intervalled_job is not None:
            all_jobs = [
                j
                for j in all_jobs
                if (filter_intervalled_job and j.interval_params)
                or (not filter_intervalled_job and not j.interval_params)
            ]
        if filter_job_state is not None:
            all_jobs = [o for o in all_jobs if o.get_state() == filter_job_state]
        return list(all_jobs)

    async def count(
        self,
        filter_user_id: Optional[UUID] = None,
        filter_job_state: Optional[WorkerJobState] = None,
        filter_tags: Optional[List[str]] = None,
        filter_intervalled_job: Optional[bool] = None,
        hide_user_jobs: bool = False,
    ) -> int:
        return len(
            await self.list(
                filter_user_id=filter_user_id,
                filter_job_state=filter_job_state,
                filter_tags=filter_tags,
                filter_intervalled_job=filter_intervalled_job,
                hide_user_jobs=hide_user_jobs,
            )
        )

    async def find(
        self,
        obj: WorkerJob | WorkerJobUpdate | WorkerJobCreate,
        raise_exception_if_not_exists: Exception = None,
        raise_exception_if_more_than_one_result: Exception = None,
    ) -> List[WorkerJob]:
        """Find matching objects in the database, based on the attributes in the given "obj"

        Args:
            obj (GenericCRUDReadType): _description_
            raise_exception_if_not_exists (Exception, optional): _description_. Defaults to None.
        """
        tbl = self.get_table_cls()
        query = select(tbl)

        for attr, val in obj.model_dump().items():
            if isinstance(val, (dict, list)):
                # json value. Postgres seems to not support json comparison atm?!?!
                # https://github.com/sqlalchemy/sqlalchemy/issues/5575#issuecomment-691121030
                # we will match WorkerJob.tags on python level
                continue

            else:
                query = query.where(getattr(tbl, attr) == val)
        res = await self.session.exec(query)
        query_result_objs: List[WorkerJob] = res.all()

        # Tag filtering
        result_objs: List[WorkerJob] = []
        if obj.tags:
            for robj in query_result_objs:
                if set(obj.tags) == set(robj.tags):
                    result_objs.append(robj)
        else:
            result_objs = query_result_objs

        if len(query_result_objs) == 0 and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        elif len(query_result_objs) > 1 and raise_exception_if_more_than_one_result:
            raise raise_exception_if_more_than_one_result
        return query_result_objs
