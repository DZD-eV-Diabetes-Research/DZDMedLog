from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Dict,
    TYPE_CHECKING,
)
from sqlmodel import Field, Column, JSON
import datetime
import uuid
from enum import Enum
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseModel, BaseTable


log = get_logger()
config = Config()


class WorkerJobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    SUCCESS = "success"


class WorkerJobCreate(MedLogBaseModel, table=False):
    id: Optional[uuid.UUID] = Field(
        description="The job id will be automaticly generated, on the backend. If there is a need to know it inbefore it can be provied here. Otherwise just leave it as `None`.",
        default=None,
    )
    task_name: str = Field(description="Class that will executed as task.")
    task_params: Optional[Dict] = Field(default_factory=dict, sa_column=Column(JSON))
    user_id: Optional[uuid.UUID] = Field(
        foreign_key="user.id",
        description="If Job was triggered by a certain user this should contain the users id, otherwise its a system job.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="A list of strings, can help to categorize, filter and/or find specific jobs or job categories.",
        sa_column=Column(JSON),
    )
    interval_params: Optional[Dict[str, int]] = Field(
        description="If the task needs to rerun in an interval define dictonary of apscheduler params as strings (https://apscheduler.readthedocs.io/en/3.x/modules/triggers/interval.html#module-apscheduler.triggers.interval). If nothing is set the task will runce once and the job will be cleaned up.",
        default=None,
        sa_column=Column(JSON),
    )


class WorkerJobUpdate(MedLogBaseModel, table=False):
    id: Optional[uuid.UUID | str] = Field(
        description="Provide the id of an WorkerJob to be updated. If non is provided, one must provide the id to the crud update method."
    )
    run_started_at: Optional[datetime.datetime] = None
    run_finished_at: Optional[datetime.datetime] = None
    error: Optional[str] = None
    result: Optional[str] = None


class WorkerJob(WorkerJobCreate, WorkerJobUpdate, BaseTable, table=True):
    __tablename__ = "worker_job"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )

    @property
    def state(self) -> WorkerJobState:
        if self.error is not None:
            return WorkerJobState.FAILED
        elif self.run_started_at is None and self.run_finished_at is None:
            return WorkerJobState.QUEUED
        elif self.run_started_at is not None and self.run_finished_at is None:
            return WorkerJobState.RUNNING
        elif self.run_started_at is not None and self.run_finished_at is not None:
            return WorkerJobState.SUCCESS
