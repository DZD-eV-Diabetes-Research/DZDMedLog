from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Dict
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
from medlogserver.model._base_model import MedLogBaseModel, BaseTable, TimestampModel
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
        results = await self.session.exec(statement=query)
        all_jobs = results.all()
        # json quering is very finicky on certain databases. lets do filtering on python side

        if filter_tags:
            all_jobs = [j for j in all_jobs if bool(set(j.tags) == set(filter_tags))]

        if filter_intervalled_job is not None:
            all_jobs = [
                j
                for j in all_jobs
                if (filter_intervalled_job and j.interval_params)
                or (not filter_intervalled_job and not j.interval_params)
            ]
        if filter_job_state is not None:
            all_jobs = [o for o in all_jobs if o.get_state() == filter_job_state]
        return all_jobs

        ### old code with json querying on db side. Can be removed on next review

        for f_tag in filter_tags:
            query = query.filter(col(WorkerJob.tags).contains(f_tag))

        if filter_intervalled_job is not None:
            if filter_intervalled_job == True:
                query = query.where(
                    is_not(WorkerJob.interval_params, None),
                    # and_(
                    #    is_not(WorkerJob.interval_params, None),
                    #    is_not(WorkerJob.interval_params, {}),
                    # )
                )
            elif filter_intervalled_job == False:
                query = query.where(
                    is_(WorkerJob.interval_params, None),
                    # or_(
                    #    is_(WorkerJob.interval_params, None),
                    #    is_(WorkerJob.interval_params, {}),
                    # )
                )
        log.info(f"DO STUFF 1: {query}")
        results = await self.session.exec(statement=query)
        log.info("DO STUFF 2")

        if filter_job_state is not None:
            result_objs = [
                o for o in results.all() if o.get_state() == filter_job_state
            ]
        else:
            result_objs = results.all()
        log.info("DO STUFF 3")
        return result_objs

    async def count(
        self,
        filter_user_id: Optional[UUID] = None,
        filter_job_state: Optional[WorkerJobState] = None,
        filter_tags: Optional[List[str]] = None,
        filter_intervalled_job: Optional[bool] = None,
        hide_user_jobs: bool = False,
    ) -> Sequence[WorkerJob]:
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
    ) -> Sequence[WorkerJob]:
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
