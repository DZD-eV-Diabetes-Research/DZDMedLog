from typing import List, Callable, Awaitable, Optional, Type
import datetime
import traceback
import pathlib
from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import (
    WorkerJob,
    WorkerJobCreate,
    WorkerJobUpdate,
    WorkerJobState,
)
from medlogserver.worker.tasks import Tasks, import_task_class
from medlogserver.worker.task import TaskBase
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class WorkerAdHocJobRunner:
    def __init__(
        self, delete_finished_jobs_after_n_minutes: Optional[int] = 60 * 24 * 7
    ):

        self.delete_finished_jobs_after_n_minutes = delete_finished_jobs_after_n_minutes

    async def run(self) -> List[WorkerJob]:
        """Pick up all queued jobs and run them once.
        This is not a re-running loop. It must be called in an intervall.

        Returns:
            List[WorkerJob]: All finished (Succeeded and Failed) jobs.
        """
        # log.debug("Start background adhoc job runner...")
        try:
            queued_jobs = await self._pick_up_queued_jobs()
            finished_jobs = await self._process_jobs(queued_jobs)
            await self._tidy_up_old_jobs()
            # log.debug("...finished background adhoc job runner.")
            if finished_jobs:

                return f"Jobs that did run {finished_jobs}"
            else:
                return None
        except Exception as error:
            # Lost some error raises. lets log explicit. To be investigated what happend here...
            log.error(error, exc_info=True)
            raise error

    async def _get_jobs(
        self, filter_job_state: Optional[WorkerJobState]
    ) -> List[WorkerJob]:
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                worker_job_crud: WorkerJobCRUD = worker_job_crud
                return await worker_job_crud.list(
                    filter_job_state=filter_job_state, filter_intervalled_job=False
                )

    async def _pick_up_queued_jobs(self) -> List[WorkerJob]:
        return await self._get_jobs(filter_job_state=WorkerJobState.QUEUED)

    async def _process_jobs(self, jobs: List[WorkerJob]) -> List[WorkerJob]:
        finished_jobs: List[WorkerJob] = []
        for job in jobs:
            # Type[TaskBase]
            log.info(f"Run adhoc job {job.task_name}...")
            job_task_class = import_task_class(Tasks[job.task_name].value)
            job_task = job_task_class(
                job=job, task_params=job.task_params, instant_run=False
            )
            await job_task.job_start()
            log.info(f"Adhoc Job {job.task_name} done.")
        return finished_jobs

    async def _tidy_up_old_jobs(self):
        if self.delete_finished_jobs_after_n_minutes:
            max_age_sec = self.delete_finished_jobs_after_n_minutes * 60
            failed_jobs = await self._get_jobs(filter_job_state=WorkerJobState.FAILED)
            succeeded_jobs = await self._get_jobs(
                filter_job_state=WorkerJobState.SUCCESS
            )
            for job in failed_jobs + succeeded_jobs:
                # HOTFIX: sqlite doesnot support timezone aware dates(?)
                if job.run_finished_at.tzinfo is None:
                    job.run_finished_at = job.run_finished_at.replace(
                        tzinfo=datetime.UTC
                    )
                job_age: datetime.timedelta = (
                    datetime.datetime.now(tz=datetime.UTC) - job.run_finished_at
                )
                if job_age.total_seconds() > max_age_sec:
                    log.debug(f"Remove obsolete job {job}")
                    job_task_class = import_task_class(Tasks[job.task_name].value)
                    await job_task_class(
                        job=job, task_params=job.task_params, instant_run=False
                    ).clean_up()
                    await self._delete_job(job)

    async def _delete_job(self, job: WorkerJob):
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                crud: WorkerJobCRUD = worker_job_crud
                await crud.delete(job.id)


class TaskRunAdHocJobs(TaskBase):
    async def work(self):
        runner = WorkerAdHocJobRunner(
            delete_finished_jobs_after_n_minutes=config.BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN
        )
        return await runner.run()
