from typing import Dict, List
import asyncio
import datetime
import traceback
from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import WorkerJob, WorkerJobUpdate
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class TaskBase:
    def __init__(
        self,
        job: WorkerJob,
        task_params: Dict = None,
        instant_run: bool = False,
    ):
        self.job = job
        self.task_params = task_params
        if instant_run:
            event_loop = asyncio.get_event_loop()
            event_loop.create_task(self.start())

    async def start(self):
        log.info(f"Run job: {self.job}")
        self.job.run_started_at = datetime.datetime.now(tz=datetime.UTC)
        self.job = await self._update_job(self.job)
        error = None
        result = None
        try:
            result = await self.work(**self.task_params)
        except Exception as error:
            log.error(f"Job '{self.job}' failed. Error: {str(error)}", exc_info=True)
            error = repr(traceback.format_exc())

        await self._finish(result, error)

    async def work(self):
        raise NotImplementedError()

    async def _finish(self, result: str = None, error: str = None):
        job_update = WorkerJobUpdate(
            id=self.job.id,
            run_finished_at=datetime.datetime.now(tz=datetime.UTC),
            result=result,
            error=error,
        )
        await self._update_job(job_update)

    async def _update_job(self, job: WorkerJobUpdate | WorkerJob) -> WorkerJob:
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                crud: WorkerJobCRUD = worker_job_crud
                job = await crud.update(job)
                return job

    async def clean_up(self):
        """Will be called when the job gets tied up (Removed from the database after running and 'config.BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN' has passed)
        Can be used to remove files from the db"""
        pass
