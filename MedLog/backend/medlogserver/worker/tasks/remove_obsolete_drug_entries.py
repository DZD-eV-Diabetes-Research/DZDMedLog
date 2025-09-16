from typing import List
import datetime

from sqlmodel import select, or_, delete, column
from sqlalchemy.sql.operators import is_

#
from medlogserver.worker.task import TaskBase
from medlogserver.db._session import get_async_session_context
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.intake import Intake

log = get_logger()
config = Config()


class RemoveObsoleteDrugDataEntries:
    async def remove_obsolete_drug_entries(self):
        async with get_async_session_context() as session:
            # find all drug that are not connected to any interview-intake and are stored in old/non-active drug datasets
            data_set_versions_disabled_and_non_cleaned_drug_query = select()
            statement_obsolete_drugs = (
                select(DrugData)
                .join(
                    DrugDataSetVersion,
                    DrugData.source_dataset_id == DrugDataSetVersion.id,
                )
                .outerjoin(Intake, DrugData.id == Intake.drug_id)
                .where(
                    or_(
                        is_(DrugDataSetVersion.current_active, False),
                        is_(DrugDataSetVersion.current_active, None),
                    )
                )
                .where(is_(Intake.id, None))
            )
            result_obsolete_drugs = await session.exec(statement_obsolete_drugs)
            obsolete_drugs = result_obsolete_drugs.all()
            obsolete_drugs_ids = [d.id for d in obsolete_drugs]
            delete_statement = delete(DrugData).where(
                column(DrugData.id)._in(obsolete_drugs_ids)
            )
            await session.exec(delete_statement)
            await session.commit()


class TaskRemoveOnbsoleteDrugDataEntries(TaskBase):
    async def work(self):
        log.debug(
            "Run Background Task: Remove obsolete unused drug database entries..."
        )
        await RemoveObsoleteDrugDataEntries().remove_obsolete_drug_entries()
        log.debug(
            "Done Background Task: Remove obsolete unused drug database entries..."
        )
