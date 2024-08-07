from typing import Literal, Dict, List, Any
from pathlib import Path, PurePath
import json
import shutil
import csv
import uuid
from pydantic import BaseModel
from medlogserver.utils import JSONEncoderMedLogCustom
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

from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class ExportIntakeContainer(BaseModel):
    event: EventExport
    interview: InterviewExport
    intake: IntakeExport


class ExportContainer(BaseModel):
    study: StudyExport
    intakes: List[ExportIntakeContainer]

    def to_flat_dict(self, include_study_data_each_row: bool = False) -> Dict[str, Any]:
        values = []
        for intake in self.intakes:
            row = {}
            for obj, obj_class_name in [
                (self.study, "study"),
                (intake.event, "event"),
                (intake.interview, "interview"),
                (intake.intake, "intake"),
            ]:
                obj: BaseModel = obj
                if not include_study_data_each_row and obj_class_name == "study":
                    continue
                # obj_class_name = obj.__class__.__name__.lower()
                for prop_name, prop_value in obj.model_dump().items():

                    if not prop_name.startswith(obj_class_name):
                        row[f"{obj_class_name}_{prop_name}"] = prop_value
                    else:
                        row[prop_name] = prop_value
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
                flatten_export_data = exportdata.to_flat_dict(
                    include_study_data_each_row=True
                )

                writer = csv.writer(target_file)
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
                study = await study_crud.get(study_id=self.study_id)
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
                    export_data.intakes.append(
                        ExportIntakeContainer(
                            study=study_data,
                            event=event_data,
                            interview=interview_data,
                            intake=intake_data,
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
            or self.job.last_result != ""
            and Path(config.EXPORT_CACHE_DIR) in Path(self.job.last_result)
            and Path(self.job.last_result).exists()
        ):
            shutil.rmtree(Path(self.job.last_result).parent)
