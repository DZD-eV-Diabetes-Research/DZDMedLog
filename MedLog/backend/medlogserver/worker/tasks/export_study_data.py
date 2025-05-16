from typing import Literal, Dict, List, Any
from pathlib import Path, PurePath
import json
import shutil
import csv
import uuid
from pydantic import BaseModel
from medlogserver.utils import path_is_parent
from medlogserver.worker.task import TaskBase
from medlogserver.db._session import get_async_session_context
from medlogserver.db import (
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
    EventCRUD,
    InterviewCRUD,
    IntakeCRUD,
)
from medlogserver.api.routes.routes_drug import get_drug
from medlogserver.model import (
    IntakeExport,
    Intake,
    EventExport,
    Event,
    StudyExport,
    Study,
    InterviewExport,
    Interview,
)
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugAPIRead,
    CustomDrugAPIRead,
    drug_to_drugAPI_obj,
    DrugData,
)
from medlogserver.db.drug_data.drug import DrugCRUD
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class DrugCodesExport(BaseModel):
    drug_code_system_name: str
    drug_code: str


class ExportIntakeContainer(BaseModel):
    event: EventExport
    interview: InterviewExport
    intake: IntakeExport
    drug_codes: List[DrugCodesExport]


class ExportContainer(BaseModel):
    study: StudyExport
    intakes: List[ExportIntakeContainer]

    def to_flat_dict(
        self,
        include_study_data_each_row: bool = False,
    ) -> Dict[str, Any]:
        values = []
        for intake in self.intakes:
            row = {}
            for objs, obj_class_name, pivot_by_column in [
                (self.study, "study", None),
                (intake.event, "event", None),
                (intake.interview, "interview", None),
                (intake.intake, "intake", None),
                (intake.drug_codes, "drug", "drug_code_system_name"),
            ]:
                objs: BaseModel | List[BaseModel] = objs
                if not include_study_data_each_row and obj_class_name == "study":
                    continue
                if not isinstance(objs, list):
                    objs = [objs]
                # obj_class_name = obj.__class__.__name__.lower()
                for obj in objs:

                    for prop_name, prop_value in obj.model_dump(
                        exclude=[pivot_by_column]
                    ).items():
                        column_name = f"{obj_class_name}_{prop_name}"
                        if prop_name.startswith(obj_class_name):
                            column_name = prop_name
                        if pivot_by_column:
                            list_column_att = getattr(obj, pivot_by_column)
                            column_name = f"{column_name}_{list_column_att}".lower()
                        row[column_name] = prop_value

            values.append(row)
        return values


class StudyDataExporter:

    def __init__(
        self, study_id: uuid.UUID, format_: Literal["csv", "json"], target_file: Path
    ):
        self.study_id = study_id
        self.format = format_
        self.target_file = target_file
        self.events: List[Event] = []
        self.interviews: List[Interview] = []

    async def run(self) -> str:
        job_result = await self.export_data_and_write_to_file()
        return str(job_result)

    async def export_data_and_write_to_file(self) -> Path:
        exportdata: ExportContainer = await self._gather_export_data()
        Path(self.target_file.parent).mkdir(parents=True, exist_ok=True)
        if self.format == "json":
            with open(self.target_file, "w", encoding="utf-8") as target_file:
                target_file.write(exportdata.model_dump_json(indent=4))
        elif self.format == "csv":
            with open(self.target_file, "w", encoding="utf-8") as target_file:
                log.debug(f"exportdata {exportdata}")
                flatten_export_data = exportdata.to_flat_dict(
                    include_study_data_each_row=True
                )
                # log.debug(f"flatten_export_data: {flatten_export_data}")

                writer = csv.writer(target_file)
                log.debug(
                    f"flatten_export_data: {flatten_export_data} \n type: {flatten_export_data}"
                )
                if flatten_export_data:
                    writer.writerow(flatten_export_data[0].keys())
                for row_data in flatten_export_data:
                    writer.writerow(row_data.values())
        else:
            return None
        return self.target_file

    async def _get_study_data(self) -> StudyExport:
        async with get_async_session_context() as session:
            async with StudyCRUD.crud_context(session) as study_crud:
                study_crud: StudyCRUD = study_crud
                study: Study = await study_crud.get(study_id=self.study_id)
        return StudyExport(**study.model_dump())

    async def _get_event_data(self, event_id: uuid.UUID) -> EventExport:
        if not self.events:
            async with get_async_session_context() as session:
                async with EventCRUD.crud_context(session) as event_crud:
                    event_crud: EventCRUD = event_crud
                    events = await event_crud.list(filter_study_id=self.study_id)
                    # cast into export format
                    self.events = [EventExport(**e.model_dump()) for e in events]
        return next(e for e in self.events if e.id == event_id)

    async def _get_drug_data(self, drug_id: uuid.UUID) -> List[DrugCodesExport]:
        codes: List[DrugCodesExport] = []
        async with get_async_session_context() as session:
            async with DrugCRUD.crud_context(session) as drug_crud:
                drug_crud: DrugCRUD = drug_crud
                drug: DrugData = await drug_crud.get(drug_id, include_relations=True)

                for code in drug.codes:
                    codes.append(
                        DrugCodesExport(
                            drug_code_system_name=code.code_system.name,
                            drug_code=code.code,
                        )
                    )
        return codes

    async def _get_interview_data(self, interview_id: uuid.UUID) -> InterviewExport:
        if not self.interviews:
            async with get_async_session_context() as session:
                async with InterviewCRUD.crud_context(session) as interview_crud:
                    interview_crud: InterviewCRUD = interview_crud
                    interviews = await interview_crud.list(
                        filter_study_id=self.study_id
                    )
                    # cast into export format
                    self.interviews = [
                        InterviewExport(**i.model_dump()) for i in interviews
                    ]
        return next(i for i in self.interviews if i.id == interview_id)

    async def _gather_export_data(self) -> List[ExportContainer]:
        study_data = await self._get_study_data()
        export_data: ExportContainer = ExportContainer(study=study_data, intakes=[])

        async with get_async_session_context() as session:
            async with IntakeCRUD.crud_context(session) as intake_crud:
                intake_crud: IntakeCRUD = intake_crud
                study_intakes = await intake_crud.list(filter_study_id=self.study_id)
                for intake_data in study_intakes:
                    interview_data = await self._get_interview_data(
                        interview_id=intake_data.interview_id
                    )
                    event_data = await self._get_event_data(
                        event_id=interview_data.event_id
                    )
                    drug_codes = await self._get_drug_data(drug_id=intake_data.drug_id)
                    export_data.intakes.append(
                        ExportIntakeContainer(
                            study=study_data,
                            event=event_data,
                            interview=interview_data,
                            intake=intake_data,
                            drug_codes=drug_codes,
                        )
                    )
        return export_data


async def export_study_intake_data(
    study_id: uuid.UUID | str, format: str, job_id: uuid.UUID | str
):
    log.info(f"Export study data (job_id: {job_id})...")
    if isinstance(study_id, str):
        study_id: uuid.UUID = uuid.UUID(study_id)
    import __main__

    export_cache_path = PurePath(
        config.EXPORT_CACHE_DIR, str(job_id), f"export_study_{study_id}.{format}"
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

        export_cache_path = PurePath(
            config.EXPORT_CACHE_DIR,
            str(self.job.id),
            f"export_study_{study_id}.{format_}",
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
