from typing import List, Tuple, Type
import time

from sqlmodel import SQLModel, select, and_, delete, col, func
from sqlalchemy.sql.operators import is_


#
from medlogserver.utils import get_now_datetime
from medlogserver.worker.task import TaskBase
from medlogserver.worker.tasks import Tasks
from medlogserver.db._session import get_async_session_context
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.model.worker_job import WorkerJobCreate
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValMulti,
    DrugValMultiRef,
    DrugValRef,
)
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.intake import Intake

log = get_logger(modulename="Task:DrugDataSetCleaner")
config = Config()

# Rows deleted per transaction. Keeps WAL pressure and lock duration manageable
# even when cleaning a full drug dataset (100 k+ entries with cascade child rows).
_DELETE_BATCH_SIZE = 50_000

# Upper bound for how long one job run may keep the worker busy. The background
# worker runs all jobs on a single event loop, so while we delete nothing else
# (data exports, ad-hoc jobs) can run. When the budget is used up we stop and
# queue a follow-up job instead of holding the worker hostage. See issue #331.
_MAX_RUN_SECONDS = 15 * 60


class DrugDataRemoveObsoleteDrugDataEntries:
    async def drug_data_remove_obsolete_drug_entries(self) -> bool:
        """Delete drug entries of deactivated drug dataset versions.

        Returns:
            bool: True if every deactivated dataset was cleaned completely,
                False if the run stopped early because it ran out of time budget.
        """
        deadline = time.monotonic() + _MAX_RUN_SECONDS
        async with get_async_session_context() as session:
            # Find dataset versions that are deactivated and not yet cleaned
            result_datasets = await session.exec(
                select(DrugDataSetVersion).where(
                    and_(
                        is_(DrugDataSetVersion.current_active, False),
                        is_(DrugDataSetVersion.is_custom_drugs_collection, False),
                        is_(DrugDataSetVersion.cleaned_date_datetime_utc, None),
                    )
                )
            )
            for drugdataset in result_datasets.all():
                log.info(
                    f"Clean up deactivated DrugDataSetVersion "
                    f"`{drugdataset.dataset_source_name}`.`{drugdataset.id}`"
                )

                # Count orphaned drugs (not referenced by any intake) without loading objects
                obsolete_count = (
                    await session.exec(
                        select(func.count(DrugData.id))
                        .outerjoin(Intake, DrugData.id == Intake.drug_id)
                        .where(DrugData.source_dataset_id == drugdataset.id)
                        .where(is_(Intake.id, None))
                    )
                ).one()

                log.info(
                    f"{obsolete_count} obsolete drug entries remaining for "
                    f"{drugdataset.dataset_source_name} v{drugdataset.dataset_version}. "
                    f"Deleting them in batches of up to {_DELETE_BATCH_SIZE} rows."
                )

                deleted_total = 0
                while True:
                    batch_deleted = await self._delete_one_batch(session, drugdataset)
                    if batch_deleted == 0:
                        # Nothing obsolete left, this dataset is done.
                        drugdataset.cleaned_date_datetime_utc = get_now_datetime()
                        session.add(drugdataset)
                        await session.commit()
                        log.info(
                            f"Dataset {drugdataset.dataset_source_name} "
                            f"v{drugdataset.dataset_version} fully cleaned "
                            f"({deleted_total} rows deleted this run)."
                        )
                        break
                    deleted_total += batch_deleted
                    log.info(
                        f"Deleted {batch_deleted} rows for "
                        f"{drugdataset.dataset_source_name} v{drugdataset.dataset_version} "
                        f"({max(obsolete_count - deleted_total, 0)} remaining)."
                    )
                    if time.monotonic() > deadline:
                        log.info(
                            f"Time budget of {_MAX_RUN_SECONDS}s used up while cleaning "
                            f"{drugdataset.dataset_source_name} v{drugdataset.dataset_version}. "
                            "Stopping here and queueing a follow-up job so the worker "
                            "can process other jobs in the meantime."
                        )
                        return False
        return True

    async def _delete_one_batch(self, session, drugdataset: DrugDataSetVersion) -> int:
        """Delete one batch of obsolete drugs of `drugdataset` including their child rows.

        Returns:
            int: number of deleted `drug` rows. 0 means there is nothing obsolete left.
        """
        # The same sub-select is used for every statement of this batch. It is
        # ordered by the (unique) drug id so all statements operate on exactly the
        # same set of rows, and it is only evaluated against rows that still exist,
        # so the next batch picks up where this one stopped.
        batch = (
            select(DrugData.id)
            .outerjoin(Intake, DrugData.id == Intake.drug_id)
            .where(DrugData.source_dataset_id == drugdataset.id)
            .where(is_(Intake.id, None))
            .order_by(col(DrugData.id))
            .limit(_DELETE_BATCH_SIZE)
        )

        # Child rows are deleted explicitly instead of relying on ON DELETE CASCADE.
        # SQLite runs without `PRAGMA foreign_keys=ON`, so a cascade would silently
        # do nothing there and leave orphans behind. And on PostgreSQL the cascade
        # fires a per-row trigger, while these set based deletes handle the whole
        # batch in one statement each.
        for child_model, child_column in self._child_tables():
            await session.exec(delete(child_model).where(col(child_column).in_(batch)))

        result = await session.exec(delete(DrugData).where(col(DrugData.id).in_(batch)))
        await session.commit()
        return result.rowcount

    def _child_tables(self) -> List[Tuple[Type[SQLModel], object]]:
        """All tables that reference `drug.id` and have to go when a drug goes."""
        # Imported here because the search module pulls in a large part of the db
        # layer and importing it at module level causes circular imports.
        from medlogserver.db.drug_data.drug_search import GenericSQLDrugSearchCache

        return [
            (DrugVal, DrugVal.drug_id),
            (DrugValRef, DrugValRef.drug_id),
            (DrugValMulti, DrugValMulti.drug_id),
            (DrugValMultiRef, DrugValMultiRef.drug_id),
            (DrugCode, DrugCode.drug_id),
            # The search cache is keyed by the drug id. It only holds rows for the
            # active dataset, but an index build that was interrupted mid-way can
            # leave rows of an obsolete dataset behind. Those would block the drug
            # delete on PostgreSQL, where the foreign key is enforced.
            (GenericSQLDrugSearchCache, GenericSQLDrugSearchCache.id),
        ]


class TaskRemoveOnbsoleteDrugDataEntries(TaskBase):
    async def work(self):
        log.debug(
            "Run Background Task: Remove obsolete unused drug database entries..."
        )
        finished = (
            await DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()
        )
        if not finished:
            await self._queue_follow_up_job()
        log.debug(
            "Done Background Task: Remove obsolete unused drug database entries..."
        )

    async def _queue_follow_up_job(self):
        """Queue another cleaning job to continue where this run stopped."""
        follow_up_job = WorkerJobCreate(
            task_name=Tasks(Tasks.DRUG_DATA_CLEANING).name,
            task_params=None,
            tags=["drug-cleaning", f"continuationOfJobID:{self.job.id}"],
            user_id=self.job.user_id,
        )
        async with get_async_session_context() as session:
            async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
                await worker_job_crud.create(follow_up_job)
        log.info("Queued follow-up DRUG_DATA_CLEANING job to continue the cleanup.")
