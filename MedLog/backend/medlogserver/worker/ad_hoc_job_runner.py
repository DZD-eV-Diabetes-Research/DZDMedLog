from typing import List, Callable, Awaitable, Optional
import datetime
import traceback
from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import (
    WorkerJob,
    WorkerJobCreate,
    WorkerJobUpdate,
    WorkerJobState,
)
from medlogserver.worker import Tasks
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
        log.debug("Start background adhoc job runner...")
        try:
            queued_jobs = await self._pick_up_queued_jobs()
            finished_jobs = await self._process_jobs(queued_jobs)
            await self._tidy_up_old_jobs()
            log.debug("...finished background adhoc job runner.")
            return finished_jobs
        except Exception as error:
            # Lost some error raises. lets log explicit. To be investigated what happend here...
            log.error(error, exc_info=True)
            raise error

    async def _update_job(self, job: WorkerJobUpdate | WorkerJob) -> WorkerJob:
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                crud: WorkerJobCRUD = worker_job_crud
                return crud.update(job)

    async def _get_jobs(
        self, filter_job_state: Optional[WorkerJobState]
    ) -> List[WorkerJob]:

        jobs: List[WorkerJob] = []
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                crud: WorkerJobCRUD = worker_job_crud
                jobs: List[WorkerJob] = await crud.list()
                for job in jobs:
                    if filter_job_state is None or job.state == filter_job_state:
                        jobs.append(job)
        return jobs

    async def _pick_up_queued_jobs(self) -> List[WorkerJob]:
        return await self._get_jobs(filter_job_state=WorkerJobState.QUEUED)

    async def _process_jobs(self, jobs: List[WorkerJob]) -> List[WorkerJob]:
        finished_jobs: List[WorkerJob] = []
        for job in jobs:
            job.run_started_at = datetime.datetime.now(tz=datetime.UTC)
            job = await self._update_job(job)
            try:
                job = await self._run_job(job)
            except Exception as error:
                log.error(f"Job '{job}' failed. Error: {str(error)}", exc_info=True)
                job.error = repr(traceback.format_exc())
                job = await self._update_job(job)
                finished_jobs.append(job)
                continue
            job.run_finished_at = datetime.datetime.now(tz=datetime.UTC)
            self._update_job(job)
            finished_jobs.append(job)
        return finished_jobs

    async def _run_job(self, job: WorkerJob) -> WorkerJob:
        log.info(f"Run adhoc job: {job}")
        job_func: Awaitable = Tasks[job.task].value
        await job_func(**job.params)

    async def _tidy_up_old_jobs(self):
        if self.delete_finished_jobs_after_n_minutes:
            max_age_sec = self.delete_finished_jobs_after_n_minutes * 60
            failed_jobs = await self._get_jobs(filter_job_state=WorkerJobState.FAILED)
            succeeded_jobs = await self._get_jobs(
                filter_job_state=WorkerJobState.SUCCESS
            )
            for job in failed_jobs + succeeded_jobs:
                job_age: datetime.timedelta = (
                    datetime.datetime.now(tz=datetime.UTC) - job.run_finished_at
                )
                if job_age.total_seconds() > max_age_sec:
                    log.debug(f"Remove obsolete job {job}")

    async def _delete_job(self, job: WorkerJob):
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                crud: WorkerJobCRUD = worker_job_crud
                await crud.delete(job.id)


async def run_adhoc_jobs():
    runner = WorkerAdHocJobRunner(
        delete_finished_jobs_after_n_minutes=config.BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN
    )
    await runner.run()
