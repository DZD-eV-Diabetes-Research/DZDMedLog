from typing import Literal, Dict, List, Any, Tuple, TextIO
from pathlib import Path, PurePath
import shutil
import csv
import time
import uuid
from itertools import groupby
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from medlogserver.utils import path_is_parent
from medlogserver.worker.task import TaskBase
from medlogserver.db._session import get_async_session_context
from medlogserver.db.event import EventCRUD
from medlogserver.db.intake import IntakeCRUD
from medlogserver.db.interview import InterviewCRUD
from medlogserver.db.study import StudyCRUD


from medlogserver.model import (
    IntakeExport,
    EventExport,
    StudyExport,
    Study,
    InterviewExport,
    Intake,
)
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugData,
)
from medlogserver.db.drug_data.drug import DrugCRUD
from medlogserver.worker.tasks.export_layout import (
    DrugCodesExport,
    DrugDataExport,
    ExportLayout,
    flatten_export_objects,
)
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger(modulename="Task:Export")
config = Config()

# Number of drug ids per `WHERE id IN (...)` query. Each batch costs a fixed number of
# queries (the drug itself plus one `selectinload` query per relation). 500 stays far
# below the bound parameter limit of SQLite and PostgreSQL.
DRUG_LOAD_BATCH_SIZE = 500


class ExportIntakeContainer(BaseModel):
    event: EventExport
    interview: InterviewExport
    intake: IntakeExport
    drug_codes: List[DrugCodesExport]
    drug_attrs: List[DrugDataExport]


class ExportContainer(BaseModel):
    study: StudyExport
    intakes: List[ExportIntakeContainer]

    def to_flat_rows(
        self,
        include_study_data_each_row: bool = False,
    ) -> List[Dict[str, Any]]:
        values = []
        for intake in self.intakes:
            row = {}
            if include_study_data_each_row:
                row.update(flatten_export_objects(self.study, "study"))
            row.update(flatten_export_objects(intake.event, "event"))
            row.update(flatten_export_objects(intake.interview, "interview"))
            row.update(flatten_export_objects(intake.intake, "intake"))
            row.update(
                flatten_export_objects(
                    intake.drug_codes, "drug_code", "drug_code_system_name"
                )
            )
            row.update(
                flatten_export_objects(intake.drug_attrs, "drug", "drug_attr_name")
            )
            values.append(row)
        return values


def drug_to_export_data(
    drug: DrugData,
    layout: ExportLayout,
) -> Tuple[List[DrugCodesExport], List[DrugDataExport]]:
    """Codes and attributes of `drug` for the export.

    The attributes are completed to all attributes of `layout`, in layout order.
    Attributes the drug has no value for get a null value (issue #387).
    """
    codes: List[DrugCodesExport] = []
    attrs: List[DrugDataExport] = []
    for code in drug.codes:
        codes.append(
            DrugCodesExport(
                drug_code_system_name=code.code_system.name,
                drug_code=code.code,
            )
        )

    attrs.append(
        DrugDataExport(drug_attr_name="trade_name", drug_attr_value=drug.trade_name)
    )
    attrs.append(
        DrugDataExport(
            drug_attr_name="market_access_date",
            drug_attr_value=str(drug.market_access_date),
        )
    )
    attrs.append(
        DrugDataExport(
            drug_attr_name="market_exit_date",
            drug_attr_value=str(drug.market_exit_date),
        )
    )
    attrs.append(
        DrugDataExport(
            drug_attr_name="is_custom_drug",
            drug_attr_value=str(drug.is_custom_drug),
        )
    )
    attrs.append(
        DrugDataExport(
            drug_attr_name="custom_drug_notes",
            drug_attr_value=drug.custom_drug_notes,
        )
    )

    for attr in drug.attrs:
        attrs.append(
            DrugDataExport(drug_attr_name=attr.field_name, drug_attr_value=attr.value)
        )
    for attr in drug.attrs_ref:
        attrs.append(
            DrugDataExport(
                drug_attr_name=attr.field_name,
                drug_attr_value=attr.lov_item.display
                if attr.value is not None
                else None,
                drug_attr_reference_code=attr.value,
            )
        )
    # attr_multi
    attrs_multi_sorted_by_name_and_index = sorted(
        drug.attrs_multi,
        key=lambda attr: (attr.field_name, attr.value_index),
    )

    for field_name, attr_group in groupby(
        attrs_multi_sorted_by_name_and_index,
        key=lambda attr: attr.field_name,
    ):
        values = [attr.value for attr in attr_group]
        attrs.append(
            DrugDataExport(
                drug_attr_name=field_name,
                drug_attr_value=values,
            )
        )
    # attr_multi_ref
    attrs_multi_ref_sorted_by_name_and_index = sorted(
        drug.attrs_multi_ref,
        key=lambda attr: (attr.field_name, attr.value_index),
    )

    for field_name, attr_group in groupby(
        attrs_multi_ref_sorted_by_name_and_index,
        key=lambda attr: attr.field_name,
    ):
        group_list = list(attr_group)
        attr_multi_ref_values = [
            attr.lov_item.display if attr.value is not None else None
            for attr in group_list
        ]
        attr_multi_ref_codes = [attr.value for attr in group_list]
        attrs.append(
            DrugDataExport(
                drug_attr_name=field_name,
                drug_attr_value=attr_multi_ref_values,
                drug_attr_reference_code=attr_multi_ref_codes,
            )
        )
    return codes, layout.complete_drug_attrs(attrs)


def _indent_json(json_str: str, indent: str) -> str:
    """Indent all but the first line, to nest a pretty printed JSON document.

    JSON escapes line breaks inside strings, so every real line break belongs to
    the pretty printing and can be indented safely.
    """
    return json_str.replace("\n", "\n" + indent)


class StudyDataExporter:
    """Export all intakes of a study with their interview, event and drug data.

    The export is built to scale with the study size (issue #362):

    * All data is loaded in one DB session with a fixed number of queries for study,
      events, interviews and intakes. Drugs are loaded once per *distinct* drug in
      batches of `DRUG_LOAD_BATCH_SIZE`, not once per intake row.
    * The output is written row by row instead of first building the whole export
      in memory.

    Every export of an installation has the same drug attributes (issue #387): the
    CSV header is `ExportLayout.csv_columns()`, independent of the exported drugs, and
    in the JSON export every intake lists all drug attributes of the layout, with null
    for missing values. Apart from these added columns and attributes the output is
    the same as the exporter before #362 wrote (see `tests/tests_export_performance.py`).
    """

    def __init__(
        self, study_id: uuid.UUID, format_: Literal["csv", "json"], target_file: Path
    ):
        self.study_id = study_id
        self.format = format_
        self.target_file = target_file
        self.study: StudyExport | None = None
        self.events: Dict[uuid.UUID, EventExport] = {}
        self.interviews: Dict[uuid.UUID, InterviewExport] = {}
        self.intakes: List[Intake] = []
        self.layout: ExportLayout | None = None
        self.drugs: Dict[
            uuid.UUID, Tuple[List[DrugCodesExport], List[DrugDataExport]]
        ] = {}

    async def run(self) -> str:
        job_result = await self.export_data_and_write_to_file()
        return str(job_result)

    async def export_data_and_write_to_file(self) -> Path:
        if self.format not in ("json", "csv"):
            return None
        gather_start = time.monotonic()
        await self._gather_export_data()
        log.info(
            f"Export of study '{self.study_id}': gathered {len(self.intakes)} intakes "
            f"with {len(self.drugs)} distinct drugs in "
            f"{time.monotonic() - gather_start:.2f}s"
        )
        write_start = time.monotonic()
        Path(self.target_file.parent).mkdir(parents=True, exist_ok=True)
        with open(self.target_file, "w", encoding="utf-8") as target_file:
            if self.format == "json":
                self._write_json(target_file)
            elif self.format == "csv":
                self._write_csv(target_file)
        log.info(
            f"Export of study '{self.study_id}': wrote {self.format} file in "
            f"{time.monotonic() - write_start:.2f}s"
        )
        return self.target_file

    async def _gather_export_data(self):
        self.layout = await ExportLayout.from_importer()
        async with get_async_session_context() as session:
            async with StudyCRUD.crud_context(session) as study_crud:
                study_crud: StudyCRUD = study_crud
                # `show_deactivated=True`: a deactivated study is closed for data
                # collection but stays exportable (issue #197). Without it the lookup
                # returned None and the export job died with
                # "'NoneType' object has no attribute 'model_dump'" (issue #353).
                study: Study = await study_crud.get(
                    study_id=self.study_id, show_deactivated=True
                )
                self.study = StudyExport(**study.model_dump())
            async with EventCRUD.crud_context(session) as event_crud:
                event_crud: EventCRUD = event_crud
                for e in await event_crud.list(filter_study_id=self.study_id):
                    self.events[e.id] = EventExport(**e.model_dump())
            async with InterviewCRUD.crud_context(session) as interview_crud:
                interview_crud: InterviewCRUD = interview_crud
                for i in await interview_crud.list(filter_study_id=self.study_id):
                    self.interviews[i.id] = InterviewExport(**i.model_dump())
            async with IntakeCRUD.crud_context(session) as intake_crud:
                intake_crud: IntakeCRUD = intake_crud
                self.intakes = list(
                    await intake_crud.list(filter_study_id=self.study_id)
                )
            await self._load_drugs(session)

    async def _load_drugs(self, session: AsyncSession):
        distinct_drug_ids = list(dict.fromkeys(i.drug_id for i in self.intakes))
        async with DrugCRUD.crud_context(session) as drug_crud:
            drug_crud: DrugCRUD = drug_crud
            for batch_start in range(0, len(distinct_drug_ids), DRUG_LOAD_BATCH_SIZE):
                batch = distinct_drug_ids[
                    batch_start : batch_start + DRUG_LOAD_BATCH_SIZE
                ]
                for drug in await drug_crud.list_by_ids_with_relations_any_dataset_version(
                    batch
                ):
                    self.drugs[drug.id] = drug_to_export_data(drug, self.layout)
        missing_drug_ids = [d for d in distinct_drug_ids if d not in self.drugs]
        if missing_drug_ids:
            raise ValueError(
                f"Export of study '{self.study_id}' failed: intakes reference drugs "
                f"that do not exist in the database: {missing_drug_ids}"
            )
        # Order of first appearance, `list_by_ids...` does not sort. Keeps the order of
        # unexpected extra CSV columns (see `_write_csv`) deterministic.
        self.drugs = {drug_id: self.drugs[drug_id] for drug_id in distinct_drug_ids}

    def _intake_container(self, intake: Intake) -> ExportIntakeContainer:
        interview = self.interviews[intake.interview_id]
        drug_codes, drug_attrs = self.drugs[intake.drug_id]
        return ExportIntakeContainer(
            event=self.events[interview.event_id],
            interview=interview,
            intake=intake,
            drug_codes=drug_codes,
            drug_attrs=drug_attrs,
        )

    def _write_json(self, target_file: TextIO):
        # Same document as `ExportContainer.model_dump_json(indent=4)`, but written one
        # intake at a time instead of serializing the whole study into one string.
        target_file.write("{\n")
        target_file.write(
            f'    "study": {_indent_json(self.study.model_dump_json(indent=4), " " * 4)},\n'
        )
        if not self.intakes:
            target_file.write('    "intakes": []\n}')
            return
        target_file.write('    "intakes": [\n')
        for index, intake in enumerate(self.intakes):
            if index > 0:
                target_file.write(",\n")
            intake_json = self._intake_container(intake).model_dump_json(indent=4)
            target_file.write(" " * 8 + _indent_json(intake_json, " " * 8))
        target_file.write("\n    ]\n}")

    def _write_csv(self, target_file: TextIO):
        # Study, event, interview and drug columns are the same for many rows, so they
        # are flattened once and cached. Only the intake columns are per row.
        study_columns = flatten_export_objects(self.study, "study")
        event_columns: Dict[uuid.UUID, Dict[str, Any]] = {}
        interview_columns: Dict[uuid.UUID, Dict[str, Any]] = {}
        drug_columns: Dict[uuid.UUID, Dict[str, Any]] = {}
        for drug_id, (drug_codes, drug_attrs) in self.drugs.items():
            columns = flatten_export_objects(
                drug_codes, "drug_code", "drug_code_system_name"
            )
            columns.update(flatten_export_objects(drug_attrs, "drug", "drug_attr_name"))
            drug_columns[drug_id] = columns

        # The header comes from the layout, so it does not depend on the exported
        # drugs (issue #387). Drug data the layout does not know (should not happen,
        # the drugs were imported by the same importer) is not dropped silently but
        # gets extra columns at the end.
        fieldnames: Dict[str, None] = dict.fromkeys(self.layout.csv_columns())
        for columns in drug_columns.values():
            unknown_columns = [c for c in columns if c not in fieldnames]
            if unknown_columns:
                log.warning(
                    f"Export of study '{self.study_id}': drug columns not defined by "
                    f"drug importer '{config.DRUG_IMPORTER_PLUGIN}': {unknown_columns}. "
                    "They are appended to the CSV header."
                )
                fieldnames.update(dict.fromkeys(unknown_columns))

        writer = csv.DictWriter(target_file, fieldnames=list(fieldnames), restval="")
        writer.writeheader()
        for intake in self.intakes:
            container = self._intake_container(intake)
            interview_id = container.interview.id
            event_id = container.event.id
            if event_id not in event_columns:
                event_columns[event_id] = flatten_export_objects(
                    container.event, "event"
                )
            if interview_id not in interview_columns:
                interview_columns[interview_id] = flatten_export_objects(
                    container.interview, "interview"
                )
            # `update()` in this order gives the same values on colliding names as
            # the old one-dict-per-row flattening.
            row = dict(study_columns)
            row.update(event_columns[event_id])
            row.update(interview_columns[interview_id])
            row.update(flatten_export_objects(container.intake, "intake"))
            row.update(drug_columns[intake.drug_id])
            writer.writerow(row)


async def export_study_intake_data(
    study_id: uuid.UUID | str, format: str, job_id: uuid.UUID | str
):
    log.info(f"Export study data (job_id: {job_id})...")
    if isinstance(study_id, str):
        study_id: uuid.UUID = uuid.UUID(study_id)
    import __main__

    export_cache_path = Path(
        PurePath(
            config.EXPORT_CACHE_DIR, str(job_id), f"export_study_{study_id}.{format}"
        )
    )
    exporter = StudyDataExporter(
        study_id=study_id, format_=format, target_file=export_cache_path
    )
    result = await exporter.run()
    log.info(f"Exported study data (job_id: {job_id}) to '{export_cache_path}'")
    return result


class TaskExportStudyIntakeData(TaskBase):
    async def work(self, study_id: str | uuid.UUID, format_: str):
        log.info(f"Export study data (job_id: {self.job.id})...")
        if isinstance(study_id, str):
            study_id: uuid.UUID = uuid.UUID(study_id)

        export_cache_path = Path(
            PurePath(
                config.EXPORT_CACHE_DIR,
                str(self.job.id),
                f"export_study_{study_id}.{format_}",
            )
        )
        exporter = StudyDataExporter(
            study_id=study_id, format_=format_, target_file=export_cache_path
        )
        result = await exporter.run()
        log.info(
            f"Exported study data (job_id: {self.job.id}) to '{export_cache_path}'"
        )
        return result

    async def clean_up(self):
        # delete export result file.
        # to be sure there is no falsy path in the job.last_result field and we accidentaly delete something outside of the cache dir
        # lets check if the last_result field.
        if (
            self.job.last_result is not None
            and self.job.last_result != ""
            and path_is_parent(
                Path(config.EXPORT_CACHE_DIR), Path(self.job.last_result)
            )
            and Path(self.job.last_result).exists()
        ):
            shutil.rmtree(Path(self.job.last_result).parent)
