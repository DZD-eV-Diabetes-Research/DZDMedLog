from typing import Literal, Dict, List, Any
from pathlib import Path, PurePath

import uuid
from pydantic import BaseModel

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
from medlogserver.model import Intake, Event, Study, Interview

from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class ExportDataContainer(BaseModel):
    study: Study
    event: Event
    interview: Interview
    intake: Intake

    # def _filter_values(self, obj):
    #    _block_props_config = {Study: [], Event: [], Intake: []}

    def to_flat_dict(self) -> Dict[str, Any]:
        values = {}
        for obj in [self.study, self.event, self.interview, self.intake]:
            obj: BaseModel = obj
            obj_class_name = obj.__class__.__name__.lower()
            for prop_name, prop_value in obj.model_dump().items():
                if not prop_name.startswith(obj_class_name):
                    values[f"{obj_class_name}_{prop_name}"] = prop_value
                else:
                    values[prop_name] = prop_value
        return values

    def to_dict(self) -> Dict[str, Any]:
        values = {}
        for obj in [self.study, self.event, self.interview, self.intake]:
            obj: BaseModel = obj
            obj_class_name = obj.__class__.__name__.lower()
            values[obj_class_name] = obj.model_dump()
        return values


class StudyDataExporter:
    def __init__(
        self, study_id: uuid.UUID, format: Literal["csv", "json"], target_file: Path
    ):
        self.study_id = study_id
        self.format = format
        self.target_file = target_file
        self.events: List[Event] = []
        self.interviews: List[Interview] = []

    async def run(self):
        await self._parse_provisioning_file(self.data_file)

    async def export_data(self):
        data = await self._gather_export_data()
        if self.format == "json":
            for obj in data

    async def _get_study_data(self) -> Study:
        async with get_async_session_context() as session:
            async with StudyCRUD.crud_context(session) as study_crud:
                study_crud: StudyCRUD = study_crud
                return study_crud.get(study_id=self.study_id)

    async def _get_event_data(self, event_id: uuid.UUID) -> Event:
        if not self.events:
            async with get_async_session_context() as session:
                async with EventCRUD.crud_context(session) as event_crud:
                    event_crud: EventCRUD = event_crud
                    self.events = event_crud.list(filter_study_id=self.study_id)
        return next(e for e in self.events if e.id == event_id)

    async def _get_interview_data(self, interview_id: uuid.UUID) -> Interview:
        if not self.interviews:
            async with get_async_session_context() as session:
                async with InterviewCRUD.crud_context(session) as interview_crud:
                    interview_crud: InterviewCRUD = interview_crud
                    self.interviews = interview_crud.list(filter_study_id=self.study_id)
        return next(i for i in self.interviews if i.id == interview_id)

    async def _gather_export_data(self) -> List[ExportDataContainer]:
        study_data = await self._get_study_data()
        export_data: List[ExportDataContainer] = []

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
                    export_data.append(
                        ExportDataContainer(
                            study=study_data,
                            event=event_data,
                            interview=interview_data,
                            intake=intake_data,
                        )
                    )
        return export_data


async def load_provisioning_data():
    log.info("Run export job...")
