from typing import Dict, List, Optional, Type
import uuid
from pydantic import create_model, BaseModel, Field
from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo
from pathlib import Path
import datetime
import asyncio
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS

from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase

from medlogserver.model.drug_data.importers.wido_gkv_arzneimittelindex import (
    WidoAiImporter,
)
from medlogserver.model.drug_data.drug_code import DrugCodeApiRead
from medlogserver.model.drug_data.drug_attr_field_definitions import ValueTypeCasting

# from medlogserver.model.drug_data.drug_attr import DrugAttrApiReadBase
from medlogserver.config import Config
from medlogserver.model.drug_data.drug import Drug

config = Config()


def drug_api_read_class_factory() -> Type[BaseModel]:
    """
    Dynamic creation of Pydantic classes für Drugs.
    Depening on the used drug data source (e.g Wido GKV Arnzeimittelindex) we have different attributes for Drug datasets.
    Therefor we need to create these classes dynamic depending on which drug database we imported our drug data from.
    The metadata for these classes are coming from the drug index importers in `medlogserver.model.drug_data.importers`

    Returns:
        Type[BaseModel]: _description_
    """
    importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]

    return asyncio.get_event_loop().run_until_complete(
        _get_DrugReadApiClass(importer_class=importer_class)
    )


async def _get_DrugReadApiClass(importer_class: Type[DrugDataSetImporterBase]) -> Type:

    importer = importer_class(Path(), "")
    attrs = {}
    for field_name, db_drug_field in Drug.model_fields.items():
        if field_name == "source_dataset_id":
            continue
        db_drug_field: FieldInfo = db_drug_field
        pydantic_field_attrs = {}
        if db_drug_field.default is not PydanticUndefined:
            pydantic_field_attrs["default"] = db_drug_field.default
        if db_drug_field.default_factory is not None:
            pydantic_field_attrs["default_factory"] = db_drug_field.default_factory
        if db_drug_field.description:
            pydantic_field_attrs["description"] = db_drug_field.description

        attrs[field_name] = (db_drug_field.annotation, Field(**pydantic_field_attrs))
    attrs_container_class = await _get_attrs_container_class(importer)
    attrs["attrs"] = (attrs_container_class, Field(default_factory=list))
    codes_container_class = await _get_codes_container_class(importer)
    attrs["codes"] = (codes_container_class, Field(default_factory=list))

    return create_model(f"{importer.api_name}Attrs", **attrs)


async def _get_attrs_container_class(importer: DrugDataSetImporterBase) -> Type:
    attr_fields = await importer.get_attr_field_definitions()
    attrs = {}

    for field in attr_fields:
        type_def = str
        if isinstance(field.type, ValueTypeCasting):
            type_def = field.type.value.python_type
        if field.optional:
            type_def = Optional[type_def]
        pydantic_field_attrs = {}
        pydantic_field_attrs["description"] = field.field_desc
        pydantic_field_attrs["default"] = field.default

        attrs[field.field_name] = (type_def, Field(**pydantic_field_attrs))

    """from pydantic create model docs:
    field_definitions: Attributes of the new model. They should be passed in the format:
            `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
            Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
    """

    m = create_model(f"{importer.api_name}Attrs", **attrs)
    return m


async def _get_codes_container_class(importer: DrugDataSetImporterBase) -> Type:
    code_fields = await importer.get_code_definitions()
    attrs = {}

    for field in code_fields:
        attrs[field.id] = (str, None)

    """from pydantic create model docs:
    field_definitions: Attributes of the new model. They should be passed in the format:
            `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
            Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
    """
    return create_model(f"{importer.api_name}Codes", **attrs)
