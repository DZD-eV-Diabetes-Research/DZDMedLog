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
                    f"Clean up deactivated DrugDataSetVersion `{drugdataset.dataset_source_name}`.`{drugdataset.id}`"
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
                    f"Deleting {obsolete_count} obsolete drug entries for drug dataset "
                    f"{drugdataset.dataset_source_name} in version {drugdataset.dataset_version}."
                )

                # Delete via subquery — no DrugData objects are loaded into Python memory.
                # Child rows (attrs, codes, etc.) are removed by DB-level ON DELETE CASCADE.
                await session.exec(
                    delete(DrugData).where(
                        col(DrugData.id).in_(
                            select(DrugData.id)
                            .outerjoin(Intake, DrugData.id == Intake.drug_id)
                            .where(DrugData.source_dataset_id == drugdataset.id)
                            .where(is_(Intake.id, None))
                        )
                    )
                )

                log.info(
                    f"Deleted {obsolete_count} obsolete drug entries for drug dataset "
                    f"{drugdataset.dataset_source_name} in version {drugdataset.dataset_version}."
                )

                # Bug fix: update the *instance*, not the class, so the change is persisted.
                drugdataset.cleaned_date_datetime_utc = get_now_datetime()
                session.add(drugdataset)

            await session.commit()


class TaskRemoveOnbsoleteDrugDataEntries(TaskBase):
    async def work(self):
        log.debug(
            "Run Background Task: Remove obsolete unused drug database entries..."
        )
        await DrugDataRemoveObsoleteDrugDataEntries().drug_data_remove_obsolete_drug_entries()
        log.debug(
            "Done Background Task: Remove obsolete unused drug database entries..."
        )
