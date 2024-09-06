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
from medlogserver.model.drug_data.drug_attr_field_definition import ValueTypeCasting

# from medlogserver.model.drug_data.drug_attr import DrugAttrApiReadBase
from medlogserver.config import Config
from medlogserver.model.drug_data.drug import Drug
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug_code import DrugCode

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

    # TODO: this return should be cached somehow....
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
    ref_attrs_container_class = await _get_ref_attrs_container_class(importer)
    attrs["ref_attrs"] = (ref_attrs_container_class, Field(default_factory=list))

    return create_model(f"{importer.api_name}Drug", **attrs)


async def _get_ref_attrs_container_class(importer: DrugDataSetImporterBase) -> Type:
    ref_attr_fields = await importer.get_ref_attr_field_definitions()
    ref_attrs = {}
    ref_value_model = create_model(
        f"{importer.api_name}RefAttrVal",
        id=(str | int, Field()),
        display=(str, Field()),
        ref_list=(str, Field(description="The name of the list this value references")),
    )

    for field in ref_attr_fields:
        type_def = ref_value_model
        if field.optional:
            type_def = Optional[type_def]
        pydantic_field_attrs = {}
        pydantic_field_attrs["description"] = field.field_desc
        pydantic_field_attrs["default"] = field.default

        ref_attrs[field.field_name] = (type_def, Field(**pydantic_field_attrs))

    """from pydantic create model docs:
    field_definitions: Attributes of the new model. They should be passed in the format:
            `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
            Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
    """

    m = create_model(f"{importer.api_name}RefAttrs", **ref_attrs)
    return m


async def _get_attrs_container_class(importer: DrugDataSetImporterBase) -> Type:
    attr_fields = await importer.get_attr_field_definitions()
    attrs = {}

    for field in attr_fields:
        print(type(field.type), field.type)
        print(type(field.type.value), field.type.value)
        type_def = field.type.value.python_type

        if field.optional:
            type_def = Optional[type_def]
        pydantic_field_attrs = {}
        pydantic_field_attrs["description"] = field.field_desc
        pydantic_field_attrs["default"] = field.default
        pydantic_field_attrs["examples"] = [
            field.type.value.casting_func(ex) for ex in field.examples
        ]

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


DrugAPIRead = drug_api_read_class_factory()


async def drug_to_drugAPI_obj(drug: Drug) -> Type[DrugAPIRead]:
    vals = {}
    for field_name, field_val in iter(drug):
        if field_name in ["attrs", "ref_attrs", "codes"]:
            continue
        if field_name in DrugAPIRead.model_fields.keys():
            vals[field_name] == field_val
    drug_attrs = {}
    for attr in drug.attrs:
        drug_attrs[attr.field_name] = attr.value
    drug_codes = {}
    for code in drug.codes:
        drug_codes[code.code_system_id] = code.code
    drug_ref_attrs = {}
    for attr in drug.ref_attrs:
        drug_ref_attrs[field_name] = {
            "id": attr.value,
            "display": attr.lov_entry.display,
            "ref_list": f"todo: api path to {attr.field_name} values",
        }
    vals["attrs"] = drug_attrs
    vals["codes"] = drug_codes
    vals["ref_attrs"] = drug_ref_attrs
    return DrugAPIRead.model_validate(vals)


async def drugAPI_to_drug(drug_api_obj: DrugAPIRead) -> Drug:
    if drug_api_obj.id is not None:
        raise NotImplementedError("TODO Tim: just query the existing drug")
    drug_id = uuid.uuid4()
    root_attr = {}
    for field_name, field_val in iter(drug_api_obj):
        if field_name in ["attrs", "ref_attrs", "codes"]:
            continue
        root_attr[field_name] = field_val
    drug = Drug.model_validate(root_attr)
    for attr_name, attr in iter(drug_api_obj.attrs):
        drug.attrs.append(DrugAttr(field_name=attr_name, value=attr.id))
    for attr_name, attr_val in iter(drug_api_obj.codes):
        drug.codes.append(DrugCode(code_system_id=attr_name, code=attr_val))
    for ref_attr_name, ref_attr_obj in iter(drug_api_obj.ref_attr):
        drug.ref_attrs.append(DrugRefAttr(field_name=ref_attr_name, value=ref_attr_obj))
    return drug
