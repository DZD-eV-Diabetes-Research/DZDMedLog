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
from medlogserver.db import BaseModel, User, UserAuthCreate, StudyCreate, StudyPermisson
from medlogserver.db import (
    CRUDBase,
    UserCRUD,
    UserAuthCRUD,
    StudyCRUD,
    StudyPermissonCRUD,
)

log = get_logger()
config = Config()
CRUD_classes: List[CRUDBase] = [UserCRUD, UserAuthCRUD, StudyCRUD, StudyPermissonCRUD]


async def load_provisioning_data():
    for data_source_file in config.APP_PROVISIONING_DATA_YAML_FILES:
        data_source_file: Path = to_path(data_source_file)
        if data_source_file.is_file() and data_source_file.exists():
            await parse_provisioning_file(data_source_file)


async def parse_provisioning_file(path: Path):
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
            crud_class, model_class = await get_medlog_crud_class_and_model_class(
                class_path
            )
            await load_provsioning_data_item(model_class, crud_class, class_data)


async def load_provsioning_data_item(
    model_cls: Type[BaseModel], crud_cls: Type[CRUDBase], class_data: List[Dict]
):
    for item in class_data:
        item_instance = model_cls.model_validate(item)
        async with get_async_session_context() as session:
            async with crud_cls.crud_context(session) as crud:
                crud: CRUDBase = crud
                await crud.create(item_instance)


async def get_medlog_crud_class_and_model_class(
    class_path: str,
) -> Tuple[CRUDBase, BaseModel]:
    print("class_path", class_path)
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    class_obj = getattr(module, class_name)
    for crudcls in CRUD_classes:
        print("crudcls.get_create_cls()", crudcls.get_create_cls())
        if class_obj == crudcls.get_create_cls():
            return crudcls, class_obj
    raise ValueError(f"Expected {crudcls.get_create_cls()}. did not found in {module}")