from typing import List
import asyncio
import multiprocessing
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from medlogserver.worker.tasks.refresh_token_cleaner import clean_tokens

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import WorkerJob

log = get_logger()
config = Config()


async def _inital_setup_scheduled_background_tasks(event_loop=None) -> AsyncIOScheduler:
    log.info("Setup background tasks..")
    background_jobs: List[WorkerJob] = []
    async with get_async_session_context() as session:
        async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
            worker_job_crud: WorkerJobCRUD = worker_job_crud
            background_jobs: List[WorkerJob] = await worker_job_crud.list(
                filter_intervalled_job=True
            )
    scheduler = AsyncIOScheduler(event_loop=event_loop)
    for b_job in background_jobs:
        scheduler.add_job(
            func=b_job.task,
            kwargs={"job": b_job, "task_params": {}, "instant_run": True},
            trigger=IntervalTrigger(**b_job.interval_params),
        )
    return scheduler


def _start_background_scheduler(event_loop=None):
    if event_loop is None:
        event_loop = asyncio.get_event_loop()
    background_scheduler = event_loop.run_until_complete(
        _inital_setup_scheduled_background_tasks(event_loop)
    )
    try:
        background_scheduler.start()
    except KeyboardInterrupt:
        log.info("Shutdown background worker...")
        background_scheduler.shutdown()
    log.info("Start background worker event loop")
    event_loop.run_forever()


def run_background_worker(
    run_in_extra_process: bool = True, event_loop: asyncio.AbstractEventLoop = None
):
    if run_in_extra_process:
        log.info("Start background worker in extra process...")
        background_worker_process = multiprocessing.Process(
            target=_start_background_scheduler, name="DZDMedLogBackgroundWorker"
        )
        background_worker_process.start()
        log.info(f"Started background worker (Process: {background_worker_process})")
    else:
        if event_loop is None:
            event_loop = asyncio.get_event_loop()
        event_loop.create_task(_start_background_scheduler(event_loop))
