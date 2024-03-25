from typing import List, Dict, Type, Callable, Optional, Tuple
import os
import datetime
import csv
import importlib

# import dramatiq
import asyncio
import zipfile
from pathlib import Path, PurePath
from dataclasses import dataclass
import yaml

# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.utils import to_path
from medlogserver.db._session import get_async_session_context
from medlogserver.model import (
    MedLogBaseModel,
    User,
    UserAuthCreate,
    StudyCreate,
    StudyPermisson,
    EventCreate,
    Interview,
)
from medlogserver.db._base_crud import CRUDBase
from medlogserver.db import (
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
    EventCRUD,
    InterviewCRUD,
    IntakeCRUD,
)

log = get_logger()
config = Config()
CRUD_classes: List[CRUDBase] = [
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
    EventCRUD,
    InterviewCRUD,
    IntakeCRUD,
]


class DataProvisioner:
    def __init__(self, data_file: str | Path):
        data_file: Path = to_path(data_file)
        if not data_file.is_file():
            raise ValueError(
                f"Can not provision data from '{data_file}'. Error: Not a file path."
            )
        self.data_file = to_path(data_file)

    async def run(self):
        await self._parse_provisioning_file(self.data_file)

    async def _parse_provisioning_file(self, path: Path):
        file_content: Dict = None
        with open(path) as file_obj:
            try:
                file_content = yaml.safe_load(file_obj)
            except:
                log.error(
                    "Failed parsing provisioning data file at '{path}'. Data provisining will be canceled."
                )
                raise
        if not "items" in file_content:
            raise ValueError(
                "Unexpected format in provisioning data file at '{path}'. Data provisining will be canceled."
            )

        for data_item in file_content["items"]:
            for class_path, class_data in data_item.items():
                crud_class, model_class = (
                    await self._get_medlog_crud_class_and_model_class(class_path)
                )
                await self._load_provsioning_data_item(
                    model_class, crud_class, class_data
                )

    async def _load_provsioning_data_item(
        self,
        model_cls: Type[MedLogBaseModel],
        crud_cls: Type[CRUDBase],
        class_data: List[Dict],
    ):
        log.debug(
            f"Try inserting DB provisionig data for table '{model_cls.__tablename__}' ({model_cls}). Row count: {len(class_data)}"
        )
        for item in class_data:
            item_instance = model_cls.model_validate(item)
            async with get_async_session_context() as session:
                async with crud_cls.crud_context(session) as crud:
                    crud: CRUDBase = crud
                    await crud.create(item_instance, exists_ok=True)

    async def _get_medlog_crud_class_and_model_class(
        self,
        class_path: str,
    ) -> Tuple[CRUDBase, MedLogBaseModel]:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        class_obj = getattr(module, class_name)
        for crudcls in CRUD_classes:
            if class_obj == crudcls.get_create_cls():
                return crudcls, class_obj
        raise ValueError(f"Expected '<class {class_path}>'. did not found in {module}")


async def load_provisioning_data():
    log.info("Try loading base data if configured...")
    for data_source_file in config.APP_PROVISIONING_DATA_YAML_FILES:
        data_provisioner = DataProvisioner(data_source_file)
        await data_provisioner.run()
