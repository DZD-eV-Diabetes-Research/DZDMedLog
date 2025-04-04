from typing import Dict, List, Optional, Type, Literal
import uuid
from pydantic import create_model, BaseModel, Field
from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo
from pathlib import Path
import datetime
import asyncio

from medlogserver.db.drug_data.importers import DRUG_IMPORTERS

from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase

from medlogserver.db.drug_data.importers.wido_gkv_arzneimittelindex import (
    WidoAiImporter52,
)
from medlogserver.model.drug_data.drug_code import DrugCodeApi
from medlogserver.model.drug_data.drug_attr_field_definition import ValueTypeCasting

# from medlogserver.model.drug_data.drug_attr import DrugAttrApiReadBase
from medlogserver.config import Config
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValRef,
    DrugAttrRefApiRead,
    DrugValMultiRef,
)
from medlogserver.model.drug_data.drug_code import DrugCode

config = Config()


class DrugApiReadClassFactory:
    def __init__(self):
        # TODO: this return should be cached somehow....
        self.drug_api_read_class = None
        self.importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        self.ref_value_models: Dict[str, Type[BaseModel]] = {}

    def get_drug_api_read_class(self) -> Type[BaseModel]:
        """
        Dynamic creation of Pydantic classes für Drugs.
        Depending on the used drug data source (e.g Wido GKV Arnzeimittelindex) we have different attributes for Drug datasets.
        Therefor we need to create these classes dynamic depending on which drug database we imported our drug data from.
        The metadata for these classes are coming from the drug index importers in `medlogserver.db.drug_data.importers`

        Returns:
            Type[BaseModel]: _description_
        """
        if self.drug_api_read_class is None:
            self.drug_api_read_class = asyncio.get_event_loop().run_until_complete(
                self._get_DrugReadApiClass(importer_class=self.importer_class)
            )
        return self.drug_api_read_class

    async def get_drug_api_read_class_asyncio(self) -> Type[BaseModel]:
        """
        Dynamic creation of Pydantic classes für Drugs.
        Depending on the used drug data source (e.g Wido GKV Arnzeimittelindex) we have different attributes for Drug datasets.
        Therefor we need to create these classes dynamic depending on which drug database we imported our drug data from.
        The metadata for these classes are coming from the drug index importers in `medlogserver.db.drug_data.importers`

        Returns:
            Type[BaseModel]: _description_
        """
        if self.drug_api_read_class is None:
            self.drug_api_read_class = await self._get_DrugReadApiClass(
                importer_class=self.importer_class
            )

        return self.drug_api_read_class

    async def _get_DrugReadApiClass(
        self, importer_class: Type[DrugDataSetImporterBase]
    ) -> Type:
        importer = importer_class()
        attrs = {}
        for field_name, db_drug_field in DrugData.model_fields.items():
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

            attrs[field_name] = (
                db_drug_field.annotation,
                Field(**pydantic_field_attrs),
            )

        codes_container_class = await self._get_codes_container_class(importer)
        attrs["codes"] = (codes_container_class, Field(default_factory=dict))

        attrs_container_class = await self._get_attrs_submodel(importer)
        attrs["attrs"] = (
            attrs_container_class,
            Field(
                default_factory=dict,
                description="Scalar Drug attributes. One value only per drug attribute.",
            ),
        )

        attrs_multi_container_class = await self._get_attrs_multi_submodel(importer)
        attrs["attrs_multi"] = (
            attrs_multi_container_class,
            Field(
                default_factory=dict,
                description="All Drug attributes that can have multiple values. e.g. something like 'Keywords'. Will always be a list.",
            ),
        )
        attrs_ref_container_class = await self._get_attrs_ref_submodel(importer)
        attrs["attrs_ref"] = (
            attrs_ref_container_class,
            Field(
                default_factory=dict,
                description="All Drug attributes reference an existing list (value + display Value. Aka SelectList).",
            ),
        )

        attrs_multi_ref_container_class = await self._get_attrs_multi_ref_submodel(
            importer
        )
        attrs["attrs_multi_ref"] = (
            attrs_multi_ref_container_class,
            Field(
                default_factory=dict,
                description="All Drug attributes that can have a list of values. These values must reference an existing list.",
            ),
        )

        return create_model(f"Drug", **attrs)

    async def _get_attrs_submodel(
        self,
        importer: DrugDataSetImporterBase,
    ) -> Type[BaseModel]:
        attr_fields = await importer.get_attr_field_definitions()
        attrs = {}

        for field in attr_fields:
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

        m = create_model(f"Attrs", **attrs)
        return m

    async def _get_attrs_ref_submodel(
        self, importer: DrugDataSetImporterBase, as_multi_ref: bool = False
    ) -> Type[BaseModel]:
        """Example output of `_get_attrs_ref_container_class`
        class AttrRef(BaseModel):
            class AttrRefDarreichungsform:
                value: int = Field(...)
                display: str= Field(...)
                ref_list: str= Field(...)

            class AttrRefSizes:
                value: int= Field(...)
                display: str= Field(...)
                ref_list: str= Field(...)

            darreichungsform: AttrRefDarreichungsform
            sizes: AttrRefSizes
        """
        attr_ref_fields = None
        if as_multi_ref:
            attr_ref_fields = await importer.get_attr_multi_ref_field_definitions()
        else:
            attr_ref_fields = await importer.get_attr_ref_field_definitions()

        attrs_ref = {}

        for field in attr_ref_fields:
            model_name = f"{'Multi' if as_multi_ref else ''}AttrRefVal{field.field_name.capitalize()}"
            value_type = field.type.value.python_type
            ref_list_api_path = f"/v2/drug/field_def/{field.field_name}/refs"
            if field.optional:
                value_type = Optional[value_type]
            ref_value_model = create_model(
                model_name,
                value=(
                    value_type,
                    Field(default=field.default, description=field.desc),
                ),
                display=(Optional[str], Field(default=None)),
                ref_list=(
                    Literal[ref_list_api_path],
                    Field(
                        default=ref_list_api_path,
                        description="The API path to the list this value references",
                    ),
                ),
            )

            type_def = List[ref_value_model] if as_multi_ref else ref_value_model
            if field.optional:
                type_def = Optional[type_def]
            pydantic_field_attrs = {}
            pydantic_field_attrs["description"] = field.field_desc
            if as_multi_ref:
                pydantic_field_attrs["default"] = (
                    [] if field.default is None else field.default
                )
            else:
                pydantic_field_attrs["default"] = field.default

            attrs_ref[field.field_name] = (type_def, Field(**pydantic_field_attrs))

        """from pydantic create model docs:
        field_definitions: Attributes of the new model. They should be passed in the format:
                `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
                Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
        """
        m = create_model(f"{'Multi' if as_multi_ref else ''}AttrRefs", **attrs_ref)
        return m

    async def _get_attrs_multi_submodel(
        self,
        importer: DrugDataSetImporterBase,
    ) -> Type[BaseModel]:
        """example output of _get_attrs_multi_container_class
        class AttrMulti(BaseModel):
            keywords: List[str] = Field(default=list,description="keywords of drug", examples[["Upper","Downer","Weird Stuff"]])
            sizes: List[float]= Field(default=list,description="Possible sizes of delivery palletes in meters", examples[[1.1,1.2,1.3]])
        """
        attr_fields = await importer.get_attr_multi_field_definitions()
        attrs = {}
        for field in attr_fields:
            type_def = List[field.type.value.python_type]
            # if field.optional:
            #    type_def = List[type_def]
            pydantic_field_attrs = {}
            pydantic_field_attrs["description"] = field.field_desc
            pydantic_field_attrs["default"] = field.default
            pydantic_field_attrs["examples"] = [field.examples]

            attrs[field.field_name] = (type_def, Field(**pydantic_field_attrs))

        """from pydantic create model docs:
        field_definitions: Attributes of the new model. They should be passed in the format:
                `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
                Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
        """

        m = create_model(f"AttrsMulti", **attrs)
        return m

    async def _get_attrs_multi_ref_submodel(
        self,
        importer: DrugDataSetImporterBase,
    ) -> Type[BaseModel]:
        """
        class AttrMultiRef(BaseModel):
            class AttrMultiRefValKeywords:
                value: int = Field(...)
                display: str = Field(...)
                ref_list: str = Field(...)

            keywords: List[AttrRefDarreichungsform]
        """
        return await self._get_attrs_ref_submodel(importer, as_multi_ref=True)
        attr_ref_fields = await importer.get_attr_ref_field_definitions()
        attrs_ref = {}

        for field in attr_ref_fields:
            model_name = f"RefAttrMultiVal{field.field_name.capitalize()}"
            value_type = field.type.value.python_type
            ref_list_api_path = f"/v2/drug/field_def/{field.field_name}/refs"
            if field.optional:
                value_type = Optional[value_type]
            ref_value_model = create_model(
                model_name,
                value=(
                    value_type,
                    Field(default=field.default, description=field.desc),
                ),
                display=(Optional[str], Field(default=None)),
                ref_list=(
                    Literal[ref_list_api_path],
                    Field(
                        default=ref_list_api_path,
                        description="The API path to the list this value references",
                    ),
                ),
            )

            type_def = List[ref_value_model]
            if field.optional:
                type_def = Optional[type_def]
            pydantic_field_attrs = {}
            pydantic_field_attrs["description"] = field.field_desc
            pydantic_field_attrs["default"] = field.default

            attrs_ref[field.field_name] = (type_def, Field(**pydantic_field_attrs))

        """from pydantic create model docs:
        field_definitions: Attributes of the new model. They should be passed in the format:
                `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
                Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
        """

        m = create_model(f"{importer.api_name}AttrRefs", **attrs_ref)
        return m

    async def _get_codes_container_class(
        self, importer: DrugDataSetImporterBase
    ) -> Type:
        code_fields = await importer.get_code_definitions()
        attrs = {}

        for field in code_fields:
            attrs[field.id] = (str, None)

        """from pydantic create model docs:
        field_definitions: Attributes of the new model. They should be passed in the format:
                `<name>=(<type>, <default value>)`, `<name>=(<type>, <FieldInfo>)`, or `typing.Annotated[<type>, <FieldInfo>]`.
                Any additional metadata in `typing.Annotated[<type>, <FieldInfo>, ...]` will be ignored.
        """
        return create_model(f"Codes", **attrs)


drug_read_api_factory = DrugApiReadClassFactory()
DrugAPIRead = drug_read_api_factory.get_drug_api_read_class()


# async def drug_to_drugAPI_obj(drug: Drug) -> DrugAPIRead:
async def drug_to_drugAPI_obj(drug: DrugData) -> Dict:
    vals = {}
    for field_name, field_val in iter(drug):
        if field_name in [
            "attrs",
            "attrs_ref",
            "attrs_multi",
            "attrs_multi_ref",
            "codes",
        ]:
            continue
        if field_name in DrugAPIRead.model_fields.keys():
            vals[field_name] = field_val

    drug_codes = {}
    for code in drug.codes:
        drug_codes[code.code_system_id] = code.code

    drug_attrs = {}
    for attr in drug.attrs:
        drug_attrs[attr.field_name] = attr.value

    drug_attrs_multi = {}
    for attr in drug.attrs_multi:
        if attr.field_name not in drug_attrs_multi:
            drug_attrs_multi[attr.field_name] = []
        drug_attrs_multi[attr.field_name].append(attr.value)

    drug_attrs_ref = {}
    for attr_ref in drug.attrs_ref:
        lov_item = attr_ref.lov_item
        drug_attrs_ref[attr_ref.field_name] = {
            "value": attr_ref.value,
            "display": lov_item.display if lov_item is not None else None,
            # "ref_list": f"/v2/drug/field_def/{attr_ref.field_name}/refs", #<- Is auto filled by class defintion now
        }

    drug_attrs_multi_ref: Dict[str, List[DrugValMultiRef]] = {}
    for attr_multi_ref in drug.attrs_multi_ref:
        if attr_multi_ref.field_name not in drug_attrs_multi_ref:
            drug_attrs_multi_ref[attr_multi_ref.field_name] = []
        lov_item = attr_multi_ref.lov_item
        drug_attrs_multi_ref[attr_multi_ref.field_name].append(
            {
                "value": attr_multi_ref.value,
                "display": lov_item.display if lov_item is not None else None,
            }
        )

    vals["codes"] = drug_codes
    vals["attrs"] = drug_attrs
    vals["attrs_ref"] = drug_attrs_ref
    vals["attrs_multi"] = drug_attrs_multi
    vals["attrs_multi_ref"] = drug_attrs_multi_ref
    return DrugAPIRead.model_validate(vals)


#### UNSED CODE?
# out of date anyway. if reintroduced need to be udpated to include `attrs_multi` and `attrs_multi_ref`
"""
async def drugAPI_to_drug(drug_api_obj: DrugAPIRead) -> Drug:
    if drug_api_obj.id is not None:
        raise NotImplementedError("TODO Tim: just query the existing drug")
    drug_id = uuid.uuid4()
    root_attr = {}
    for field_name, field_val in iter(drug_api_obj):
        if field_name in ["attrs", "attrs_ref", "codes"]:
            continue
        root_attr[field_name] = field_val
    drug = Drug.model_validate(root_attr)
    for attr_name, attr in iter(drug_api_obj.attrs):
        drug.attrs.append(DrugAttr(field_name=attr_name, value=attr.id))
    for attr_name, attr_val in iter(drug_api_obj.codes):
        drug.codes.append(DrugCode(code_system_id=attr_name, code=attr_val))
    for attr_ref_name, attr_ref_obj in iter(drug_api_obj.attr_ref):
        drug.attrs_ref.append(DrugAttrRef(field_name=attr_ref_name, value=attr_ref_obj))
    return drug
"""
