import datetime

from sqlmodel import select, and_, delete, col, func
from sqlalchemy.sql.operators import is_


#
from medlogserver.utils import get_now_datetime
from medlogserver.worker.task import TaskBase
from medlogserver.db._session import get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.intake import Intake

log = get_logger(modulename="Task:DrugDataSetCleaner")
config = Config()

# Rows deleted per transaction. Keeps WAL pressure and lock duration manageable
# even when cleaning a full drug dataset (100 k+ entries with cascade child rows).
_DELETE_BATCH_SIZE = 50_000


class DrugDataRemoveObsoleteDrugDataEntries:
    async def drug_data_remove_obsolete_drug_entries(self):
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
                    f"Deleting one batch of up to {_DELETE_BATCH_SIZE} rows this run."
                )

                # Delete exactly one batch per job run so the worker stays free for
                # other tasks (e.g. data exports) between runs. The scheduler will
                # call this job again and pick up the next batch automatically.
                # Child rows (attrs, codes, etc.) are removed by DB-level ON DELETE CASCADE.
                result = await session.exec(
                    delete(DrugData).where(
                        col(DrugData.id).in_(
                            select(DrugData.id)
                            .outerjoin(Intake, DrugData.id == Intake.drug_id)
                            .where(DrugData.source_dataset_id == drugdataset.id)
                            .where(is_(Intake.id, None))
                            .limit(_DELETE_BATCH_SIZE)
                        )
                    )
                )
                await session.commit()
                batch_deleted = result.rowcount
                log.info(
                    f"Deleted {batch_deleted} rows for "
                    f"{drugdataset.dataset_source_name} v{drugdataset.dataset_version} "
                    f"({obsolete_count - batch_deleted} remaining)."
                )

                if batch_deleted < _DELETE_BATCH_SIZE:
                    # Last batch — no orphaned rows left, mark dataset as cleaned.
                    drugdataset.cleaned_date_datetime_utc = get_now_datetime()
                    session.add(drugdataset)
                    await session.commit()
                    log.info(
                        f"Dataset {drugdataset.dataset_source_name} "
                        f"v{drugdataset.dataset_version} fully cleaned."
                    )
                else:
                    log.info(
                        f"Batch complete. Remaining rows will be deleted on the next job run."
                    )


class TaskRemoveOnbsoleteDrugDataEntries(TaskBase):
    async def work(self):
        log.debug(
            "Run Background Task: Remove obsolete unused drug database entries..."
        )
        await DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()
        log.debug(
            "Done Background Task: Remove obsolete unused drug database entries..."
        )
