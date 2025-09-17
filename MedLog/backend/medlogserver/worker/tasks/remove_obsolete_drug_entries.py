from typing import List
import datetime

from sqlmodel import select, or_, and_, delete, column
from sqlalchemy.sql.operators import is_

#
from medlogserver.utils import get_now_datetime
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
            query_data_set_versions_disabled_and_non_cleaned_drug = select(
                DrugDataSetVersion
            ).where(
                and_(
                    is_(DrugDataSetVersion.current_active, False),
                    is_(DrugDataSetVersion.is_custom_drugs_collection, False),
                    is_(DrugDataSetVersion.cleaned_date_datetime_utc, None),
                )
            )
            result_data_set_versions_disabled_and_non_cleaned_drug = await session.exec(
                query_data_set_versions_disabled_and_non_cleaned_drug
            )
            for (
                drugdataset
            ) in result_data_set_versions_disabled_and_non_cleaned_drug.all():
                log.info(
                    f"Clean up deactivated DrugDataSetVersion `{DrugDataSetVersion.dataset_source_name}`.`{DrugDataSetVersion.id}"
                )
                query_obsolete_drugs = (
                    select(DrugData)
                    .outerjoin(Intake, DrugData.id == Intake.drug_id)
                    .where(
                        is_(DrugData.source_dataset_id, drugdataset.id),
                    )
                    .where(is_(Intake.id, None))
                )
                result_obsolete_drugs = await session.exec(query_obsolete_drugs)
                obsolete_drugs = result_obsolete_drugs.all()
                obsolete_drugs_ids = [d.id for d in obsolete_drugs]
                delete_statement = delete(DrugData).where(
                    column(DrugData.id)._in(obsolete_drugs_ids)
                )
                await session.exec(delete_statement)
                DrugDataSetVersion.cleaned_date_datetime_utc = get_now_datetime()
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
