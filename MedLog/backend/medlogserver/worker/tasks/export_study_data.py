from typing import Literal
from pathlib import Path, PurePath

import uuid
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class StudyDataExporter:
    def __init__(self, study_id: uuid.UUID, format: Literal["csv", "json"]):
        self.study_id = study_id
        self.format = format

    async def run(self):
        await self._parse_provisioning_file(self.data_file)


async def load_provisioning_data():
    log.info("Run export job...")
