import dramatiq
import sys
import asyncio
import multiprocessing
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from medlogserver.worker.tasks.provisioning_data_loader import load_provisioning_data
from medlogserver.worker.tasks.refresh_token_cleaner import clean_tokens
from medlogserver.worker.tasks.wido_gkv_arzneimittelindex_importer import (
    import_wido_gkv_arzneimittelindex_data,
)
from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()


async def _setup_scheduled_background_tasks(event_loop=None) -> AsyncIOScheduler:
    log.info("Setup background tasks..")
    scheduler = AsyncIOScheduler(event_loop=event_loop)
    scheduler.add_job(
        func=clean_tokens,
        trigger=CronTrigger(minute="*"),
        max_instances=1,
    )
    scheduler.add_job(
        func=import_wido_gkv_arzneimittelindex_data,
        trigger=CronTrigger(minute="*"),
        max_instances=1,
    )
    return scheduler
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.shutdown()


def _start_background_scheduler(event_loop=None):
    if event_loop is None:
        event_loop = asyncio.get_event_loop()
    background_scheduler = event_loop.run_until_complete(
        _setup_scheduled_background_tasks(event_loop)
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
        event_loop.create_task(_start_background_scheduler(event_loop))
