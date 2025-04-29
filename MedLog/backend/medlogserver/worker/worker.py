from typing import List, Optional
import asyncio
import multiprocessing
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from apscheduler.triggers.interval import IntervalTrigger


from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import WorkerJob
from medlogserver.worker.tasks import Tasks, import_task_class
import threading
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


async def _inital_setup_scheduled_background_tasks() -> AsyncIOScheduler:
    log.info("Setup background tasks.....")
    background_jobs: List[WorkerJob] = []
    try:
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                c = await worker_job_crud.count()
                worker_job_crud: WorkerJobCRUD = worker_job_crud
                background_jobs: List[WorkerJob] = await worker_job_crud.list(
                    filter_intervalled_job=True
                )
            log.debug(f"Following Background jobs found for setup: {background_jobs}")
    except Exception as e:
        log.info(f"Querying Background Jobs for inital setup failed {e}")
        raise e
    scheduler = AsyncIOScheduler()
    log.debug(f"Register background job: {background_jobs}")
    for b_job in background_jobs:
        task_class = import_task_class(Tasks[b_job.task_name].value)
        log.info(
            f"Add Scheduled job {task_class} with intervall {b_job.interval_params}"
        )
        scheduler.add_job(
            func=task_class,
            kwargs={
                "job": b_job,
                "task_params": b_job.task_params,
                "instant_run": True,
            },
            trigger=IntervalTrigger(**b_job.interval_params),
        )
    return scheduler


def _start_background_scheduler(event_loop=None):
    if event_loop is None:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    background_scheduler = event_loop.run_until_complete(
        _inital_setup_scheduled_background_tasks()
    )
    try:
        log.info("[WORKER] Start background job scheduler...")
        background_scheduler._eventloop = event_loop
        background_scheduler.start()
    except KeyboardInterrupt:
        log.info("Shutdown background worker...")
        background_scheduler.shutdown()
    log.info("Start background worker event loop")
    event_loop.run_forever()


def run_background_worker(
    run_in_extra_process: bool = True,
    event_loop: Optional[asyncio.AbstractEventLoop] = None,
) -> Optional[multiprocessing.Process]:
    if run_in_extra_process:
        log.info("Start background worker in extra process...")
        background_worker_process = multiprocessing.Process(
            target=_start_background_scheduler, name="DZDMedLogBackgroundWorker"
        )
        background_worker_process.start()
        log.info(f"Started background worker (Process: {background_worker_process})")
        return background_worker_process
    else:
        if event_loop is None:
            event_loop = asyncio.get_event_loop()
        event_loop.create_task(_start_background_scheduler(event_loop))
