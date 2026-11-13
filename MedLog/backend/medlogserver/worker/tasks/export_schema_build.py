"""Build and store the export schemas (issue #387, part 2).

The schemas depend on the MedLog code (fixed export columns) and on the imported drug
dataset (reference list values), so they are built by a worker job:

* as follow-up of a successful drug data load (`TaskDrugDataLoading`),
* on startup, when no schema exists for the running MedLog version and the active
  drug dataset version (`queue_export_schema_build_if_missing()`, called by `init_db()`).

The API only reads the stored result, see `api/routes/routes_export.py`.
"""

from typing import List, Optional
import functools
import uuid

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.utils import get_version
from medlogserver.db._session import get_async_session_context
from medlogserver.db.export_schema import ExportSchemaCRUD
from medlogserver.db.worker_job import WorkerJobCRUD
from medlogserver.db.drug_data.drug_lov_values import DrugAttrFieldLovItemCRUD
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.export_schema import ExportSchema, ExportSchemaFormat
from medlogserver.model.worker_job import WorkerJobCreate, WorkerJobState
from medlogserver.worker.task import TaskBase
from medlogserver.worker.tasks import Tasks
from medlogserver.worker.tasks.export_layout import ExportLayout
from medlogserver.worker.tasks.export_schema import (
    ExportSchemaVersions,
    ReferenceValues,
    build_export_schemas,
)

log = get_logger(modulename="Task:ExportSchemaBuild")
config = Config()


@functools.cache
def medlog_version() -> str:
    """The MedLog version schemas are stored and looked up with.

    Cached per process: in a git checkout `get_version()` changes as soon as the
    working tree gets dirty, and the API would then look for a schema the worker never
    built. Both processes keep the version they started with.
    """
    return get_version()


async def get_active_drug_dataset() -> Optional[DrugDataSetVersion]:
    importer = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]()
    return await importer.get_currently_activated_dataset()


async def load_reference_values(layout: ExportLayout) -> ReferenceValues:
    """Reference list values of the small reference lists of `layout`.

    Large lists (`is_large_reference_list`) get no `enum`, it would bloat the schema.
    """
    reference_values: ReferenceValues = {}
    async with get_async_session_context() as session:
        async with DrugAttrFieldLovItemCRUD.crud_context(session) as lov_crud:
            lov_crud: DrugAttrFieldLovItemCRUD = lov_crud
            for attr in layout.drug_attrs:
                if (
                    not attr.is_reference
                    or attr.field_definition.is_large_reference_list
                ):
                    continue
                reference_values[attr.name] = (
                    await lov_crud.list_distinct_of_all_dataset_versions(
                        field_name=attr.name,
                        importer_name=attr.field_definition.importer_name,
                    )
                )
    return reference_values


async def build_and_store_export_schemas() -> Optional[ExportSchemaVersions]:
    """Build the schemas for the active drug dataset and store them.

    Returns None (and stores nothing) if no drug dataset is active yet. The drug data
    load queues a new build when it activates one.
    """
    drug_dataset = await get_active_drug_dataset()
    if drug_dataset is None:
        log.warning(
            "No active drug dataset, export schemas are not built. They are built "
            "after the first drug data import."
        )
        return None
    versions = ExportSchemaVersions(
        medlog_version=medlog_version(),
        drug_importer=config.DRUG_IMPORTER_PLUGIN,
        drug_dataset_name=drug_dataset.dataset_source_name,
        drug_dataset_version=drug_dataset.dataset_version,
    )
    layout = await ExportLayout.from_importer()
    reference_values = await load_reference_values(layout)
    schemas = build_export_schemas(layout, reference_values, versions)
    async with get_async_session_context() as session:
        async with ExportSchemaCRUD.crud_context(session) as export_schema_crud:
            export_schema_crud: ExportSchemaCRUD = export_schema_crud
            await export_schema_crud.replace_all(
                [
                    ExportSchema(
                        medlog_version=versions.medlog_version,
                        drug_dataset_version=versions.drug_dataset_version,
                        format=format_.value,
                        content=content,
                    )
                    for format_, content in schemas.items()
                ]
            )
    log.info(
        f"Built export schemas for MedLog version '{versions.medlog_version}' and "
        f"drug dataset '{versions.drug_dataset_name}' version "
        f"'{versions.drug_dataset_version}'."
    )
    return versions


async def create_export_schema_build_job(
    user_id: Optional[uuid.UUID] = None, tags: Optional[List[str]] = None
):
    job = WorkerJobCreate(
        task_name=Tasks(Tasks.EXPORT_SCHEMA_BUILD).name,
        task_params=None,
        tags=["export-schema"] + (tags or []),
        user_id=user_id,
    )
    async with get_async_session_context() as session:
        async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
            log.debug(f"Create Task ExportSchemaBuild Job {job}")
            await worker_job_crud.create(job)


async def queue_export_schema_build_if_missing():
    """Startup check: queue a build if the stored schemas do not fit the running version.

    The fixed export columns change with the MedLog code, so a new release needs new
    schemas even without a new drug import. Nothing is queued while no drug dataset is
    active (the drug data load queues the build) or while a build job is pending.
    """
    drug_dataset = await get_active_drug_dataset()
    if drug_dataset is None:
        return
    async with get_async_session_context() as session:
        async with ExportSchemaCRUD.crud_context(session) as export_schema_crud:
            export_schema_crud: ExportSchemaCRUD = export_schema_crud
            existing_formats = await export_schema_crud.list_formats(
                medlog_version=medlog_version(),
                drug_dataset_version=drug_dataset.dataset_version,
            )
        if set(existing_formats) == set(ExportSchemaFormat):
            return
        async with WorkerJobCRUD.crud_context(session) as worker_job_crud:
            worker_job_crud: WorkerJobCRUD = worker_job_crud
            pending_jobs = [
                job
                for job in await worker_job_crud.list(
                    filter_task=Tasks.EXPORT_SCHEMA_BUILD
                )
                if job.get_state() in (WorkerJobState.QUEUED, WorkerJobState.RUNNING)
            ]
    if pending_jobs:
        return
    log.info(
        f"No export schemas for MedLog version '{medlog_version()}' and drug dataset "
        f"version '{drug_dataset.dataset_version}'. Queue a build job."
    )
    await create_export_schema_build_job(tags=["init-job"])


class TaskBuildExportSchemas(TaskBase):
    async def work(self):
        versions = await build_and_store_export_schemas()
        if versions is None:
            return "No active drug dataset, no export schemas built."
        return (
            f"Built export schemas for MedLog version '{versions.medlog_version}' and "
            f"drug dataset version '{versions.drug_dataset_version}'."
        )
