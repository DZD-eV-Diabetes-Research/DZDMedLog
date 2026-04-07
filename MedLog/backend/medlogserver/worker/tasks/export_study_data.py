from typing import Literal, Dict, List, Any, Tuple, Type
from pathlib import Path, PurePath
import shutil
import csv
import uuid
from itertools import groupby
from pydantic import BaseModel
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
    Event,
    StudyExport,
    Study,
    InterviewExport,
    Interview,
)
from medlogserver.model.drug_data.api_drug_model_factory import (
    DrugData,
)
from medlogserver.db.drug_data.drug import DrugCRUD
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger(modulename="Task:Export")
config = Config()


class DrugCodesExport(BaseModel):
    drug_code_system_name: str
    drug_code: str


class ValueReferenceCodeNotApplicable:
    pass


class DrugDataExport(BaseModel):
    drug_attr_name: str
    drug_attr_value: str | List[str | None] | None
    drug_attr_reference_code: (
        str | List[str | None] | None | Type[ValueReferenceCodeNotApplicable]
    ) = ValueReferenceCodeNotApplicable


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
            for objs, obj_name, pivot_by_column in [
                (self.study, "study", None),
                (intake.event, "event", None),
                (intake.interview, "interview", None),
                (intake.intake, "intake", None),
                (intake.drug_codes, "drug_code", "drug_code_system_name"),
                (intake.drug_attrs, "drug", "drug_attr_name"),
            ]:
                objs: BaseModel | List[BaseModel] = objs
                if not include_study_data_each_row and obj_name == "study":
                    continue
                if not isinstance(objs, list):
                    objs = [objs]
                # obj_class_name = obj.__class__.__name__.lower()
                for obj in objs:
                    exclude_set = {pivot_by_column} if pivot_by_column else None
                    for prop_name, prop_value in obj.model_dump(
                        exclude=exclude_set
                    ).items():
                        log.debug(
                            f"#####{prop_name} -> prop_value {prop_value} == ValueReferenceCodeNotApplicable: {prop_value == ValueReferenceCodeNotApplicable}"
                        )
                        if prop_value == ValueReferenceCodeNotApplicable:
                            log.debug("Continue")
                            continue
                        column_name = f"{obj_name}_{prop_name}"
                        if prop_name.startswith(obj_name):
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
                flatten_export_data = exportdata.to_flat_rows(
                    include_study_data_each_row=True
                )
                if flatten_export_data:
                    fieldnames: List[str] = []
                    seen: set[str] = set()

                    for row in flatten_export_data:
                        for key in row.keys():
                            if key not in seen:
                                seen.add(key)
                                fieldnames.append(key)
                    writer = csv.DictWriter(target_file, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in flatten_export_data:
                        writer.writerow(row)
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

    async def _get_drug_data(
        self, drug_id: uuid.UUID
    ) -> Tuple[List[DrugCodesExport], List[DrugDataExport]]:
        codes: List[DrugCodesExport] = []
        attrs: List[DrugDataExport] = []
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

                attrs.append(
                    DrugDataExport(
                        drug_attr_name="trade_name", drug_attr_value=drug.trade_name
                    )
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
                        DrugDataExport(
                            drug_attr_name=attr.field_name, drug_attr_value=attr.value
                        )
                    )
                # for attr in drug.attrs_multi:
                #    attrs.append(
                #        DrugDataExport(
                #            drug_attr_name=attr.field_name,
                #            drug_attr_value=attr.value,
                #        )
                #    )
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
                    group_list = attr_group  # list(attr_group)
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

        return codes, attrs

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

    async def _gather_export_data(self) -> ExportContainer:
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
                    drug_codes, drug_attrs = await self._get_drug_data(
                        drug_id=intake_data.drug_id
                    )
                    export_data.intakes.append(
                        ExportIntakeContainer(
                            event=event_data,
                            interview=interview_data,
                            intake=intake_data,
                            drug_codes=drug_codes,
                            drug_attrs=drug_attrs,
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
