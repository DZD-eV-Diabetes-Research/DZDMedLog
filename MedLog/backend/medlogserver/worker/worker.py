from typing import List, Optional, Dict
from pathlib import Path, PurePath
import asyncio
import multiprocessing

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from apscheduler.triggers.interval import IntervalTrigger

from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlalchemy import text, ScalarResult
from sqlalchemy.exc import SQLAlchemyError

from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import WorkerJob
from medlogserver.worker.tasks import Tasks, import_task_class
from medlogserver.worker.task import task_runner

from medlogserver.utils import get_default_file_data
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


async def _wait_for_datascheme_healthy(timeout_sec=60):
    # on first time start the database may not be initialized yet. we need to wait to the `worker_job`-table to be created from the main process
    log.info("Backroundworker wait for job table to be created if neccessary...")

    start_time = asyncio.get_event_loop().time()
    # get count of default job that need to be in database
    default_data = get_default_file_data(config.APP_PROVISIONING_DEFAULT_DATA_YAML_FILE)

    default_data_items_WorkerJobCreate: Dict = [
        item
        for item in default_data["items"]
        if "medlogserver.model.worker_job.WorkerJobCreate" in item
    ][0]["medlogserver.model.worker_job.WorkerJobCreate"]
    log.debug(f"default_data_item_WorkerJobCreate {default_data_items_WorkerJobCreate}")
    # f*** this. created https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/131

    default_jobs_count_awaited = len(default_data_items_WorkerJobCreate)
    log.debug(f"default_jobs_count_awaited {default_jobs_count_awaited}")

    while True:
        try:
            async with get_async_session_context() as session:
                # Database agnostic approach: try to query the table directly
                result: ScalarResult = await session.exec(
                    text("SELECT count(*) FROM worker_job")
                )
                job_count = result.one()[0]
                log.debug(f"job_count {job_count}")
                if job_count >= default_jobs_count_awaited:
                    log.info(
                        "Backroundworker found table worker_job default jobs deployed - database schema is healthy"
                    )
                    return True
                log.debug(
                    "Backroundworker wait for default jobs in job table to be created..."
                )
        except SQLAlchemyError:
            # Table doesn't exist or other DB error - continue waiting
            pass

        # Check timeout
        if asyncio.get_event_loop().time() - start_time >= timeout_sec:
            raise TimeoutError(
                f"Database schema not ready within {timeout_sec} seconds"
            )

        await asyncio.sleep(1)


async def _inital_setup_scheduled_background_tasks() -> AsyncIOScheduler:
    await _wait_for_datascheme_healthy()
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
    scheduler = AsyncIOScheduler(
        job_defaults={"max_instances": 1},
        executors={
            "default": AsyncIOExecutor(),
        },
    )
    log.debug(f"Register background job: {background_jobs}")
    for b_job in background_jobs:
        task_class = import_task_class(Tasks[b_job.task_name].value)
        log.info(
            f"Add Scheduled job {task_class} with intervall {b_job.interval_params}"
        )
        scheduler.add_job(
            func=task_runner,
            kwargs={
                "task_class": task_class,
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
