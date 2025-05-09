from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Tuple,
    Callable,
)
from pydantic import validate_email, validator, StringConstraints
from pydantic_core import PydanticCustomError
from fastapi import Depends
import contextlib
from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import (
    Field,
    select,
    delete,
    Column,
    JSON,
    SQLModel,
    func,
    col,
    desc,
    or_,
    and_,
)
from sqlmodel.sql import expression as sqlEpression
import uuid
from uuid import UUID
from sqlalchemy.orm import selectinload

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.drug_attr import (
    DrugValRef,
    DrugVal,
    DrugValApiCreate,
    DrugValMulti,
    DrugValMultiRef,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
from medlogserver.model.drug_data.drug import DrugCustomCreate
from medlogserver.model.drug_data.drug_code import DrugCodeApi, DrugCode
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem

log = get_logger()
config = Config()

AttrNamesType = Literal["attrs", "attrs_multi", "attrs_ref", "attrs_multi_ref"]


class CustomDrugAttrNotValid(Exception):
    pass


class DrugWithCodeAllreadyExists(Exception):
    pass


class DrugCRUD(
    create_crud_base(
        table_model=DrugData,
        read_model=DrugData,
        create_model=DrugData,
        update_model=DrugData,
    )
):
    async def append_current_and_custom_drugs_dataset_version_where_clause(
        self, query: sqlEpression.Select
    ):
        drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        drug_importer = drug_importer_class()
        # todo: this probably can be optimized...

        sub_query = (
            select(DrugDataSetVersion.id)
            .where(
                DrugDataSetVersion.dataset_source_name == drug_importer.dataset_name
                and DrugDataSetVersion.is_custom_drugs_collection == False
            )
            .order_by(desc(DrugDataSetVersion.current_active))
            .order_by(desc(DrugDataSetVersion.dataset_version))
            .limit(1)
            .scalar_subquery()
        )
        sub_query_custom_drugs = (
            select(DrugDataSetVersion.id)
            .where(
                DrugDataSetVersion.dataset_source_name == drug_importer.dataset_name
                and DrugDataSetVersion.is_custom_drugs_collection == True
            )
            .limit(1)
            .scalar_subquery()
        )
        query.where(
            or_(
                DrugData.source_dataset_id == sub_query,
                DrugData.source_dataset_id == sub_query_custom_drugs,
            )
        )
        return query

    async def count(
        self,
    ) -> int:
        query = select(func.count()).select_from(DrugData)
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        filter_study_id: UUID = None,
        pagination: QueryParamsInterface = None,
        include_relations: bool = False,
    ) -> Sequence[DrugData]:
        if isinstance(filter_study_id, str):
            filter_study_id: UUID = UUID(filter_study_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(DrugData)
        if include_relations:
            query = query.options(
                selectinload(DrugData.attrs),
                selectinload(DrugData.attrs_ref).selectinload(DrugValRef.lov_item),
                selectinload(DrugData.attrs_multi_ref).selectinload(
                    DrugValMultiRef.lov_item
                ),
                selectinload(DrugData.codes),
            )
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get(
        self,
        id_: UUID,
        include_relations: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> DrugData | None:
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(DrugData)
        if include_relations:
            query = query.options(
                selectinload(DrugData.attrs),
                selectinload(DrugData.attrs_ref).selectinload(DrugValRef.lov_item),
                selectinload(DrugData.attrs_multi_ref).selectinload(
                    DrugValMultiRef.lov_item
                ),
                selectinload(DrugData.codes),
            )
        query = query.where(DrugData.id == id_)
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )
        results = await self.session.exec(statement=query)
        drug = results.one_or_none()
        if drug is None and raise_exception_if_none:
            raise raise_exception_if_none
        return drug

    async def get_multiple(
        self,
        ids: List[str],
        pagination: QueryParamsInterface = None,
        keep_result_in_ids_order: bool = True,
    ) -> Sequence[DrugData]:
        query = select(DrugData).where(col(DrugData.id).in_(ids))
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )

        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_result_in_ids_order:
            # todo: maybe we can solve the drug order in sql?
            db_order: List[DrugData] = results.all()
            new_order: List[DrugData] = []
            for drug_id in ids:
                db_order_item_index = next(
                    (i for i, obj in enumerate(db_order) if obj.id == drug_id)
                )
                item = db_order.pop(db_order_item_index)
                new_order.append(item)
            return new_order
        return results.all()

    async def create_custom(
        self, drug_create: DrugCustomCreate, custom_drug_dataset: DrugDataSetVersion
    ) -> DrugData:
        drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        drug_importer = drug_importer_class()

        new_objects = []
        new_drug_id = uuid.uuid4()

        drug = DrugData(
            id=new_drug_id,
            source_dataset_id=custom_drug_dataset.id,
            is_custom_drug=True,
            **drug_create.model_dump(
                exclude=[
                    "attrs",
                    "attrs_multi",
                    "attrs_ref",
                    "attrs_multi_ref",
                    "codes",
                ]
            ),
        )
        attr_defs = await drug_importer.get_all_attr_field_definitions()

        def find_attr_def(attr_type: AttrNamesType, field_name: str):
            try:
                return next(
                    (ad for ad in attr_defs[attr_type] if ad.field_name == field_name)
                )
            except StopIteration:
                raise CustomDrugAttrNotValid(
                    f"Attribute with name '{attr_type}.{field_name}' is not supported in current drug dataset. Available '{attr_type}'-field names are: {[ad.field_name for ad in attr_defs[attr_type]]}. Can not create custom drug."
                )

        async def find_lov_item(
            attr_type: AttrNamesType, field_name: str, val: str
        ) -> DrugAttrFieldLovItem:
            lov_item_query = select(DrugAttrFieldLovItem).where(
                and_(
                    DrugAttrFieldLovItem.field_name == field_name,
                    DrugAttrFieldLovItem.value == val,
                )
            )
            lov_item_res = await self.session.exec(lov_item_query)
            lov_item = lov_item_res.one_or_none()
            if lov_item is None:
                raise CustomDrugAttrNotValid(
                    f"Value '{val}' for ref/select attr with name '{attr_type}.{field_name}' is not a valid selection. Can not create custom drug."
                )
            return lov_item

        # attrs
        for attr_create in drug_create.attrs:
            attr_def = find_attr_def("attrs", attr_create.field_name)
            drug.attrs.append(
                DrugVal(
                    field_name=attr_def.field_name,
                    value=attr_create.value,
                    importer_name=config.DRUG_IMPORTER_PLUGIN,
                )
            )
        # attrs_ref
        for attr_ref_create in drug_create.attrs_ref:
            attr_ref_def = find_attr_def("attrs_ref", attr_ref_create.field_name)
            lov_item = await find_lov_item(
                "attrs_ref", attr_ref_def.field_name, attr_ref_create.value
            )
            drug.attrs_ref.append(
                DrugValRef(
                    field_name=attr_ref_def.field_name,
                    value=attr_ref_create.value,
                    # lov_item=lov_item,
                    importer_name=config.DRUG_IMPORTER_PLUGIN,
                )
            )
        # attrs_multi
        for attr_multi_create in drug_create.attrs_multi:
            attr_multi_def = find_attr_def("attrs_multi", attr_multi_create.field_name)
            if attr_multi_create.values is None:
                continue
            for index, multi_val in enumerate(attr_multi_create.values):
                drug.attrs_multi.append(
                    DrugValMulti(
                        value_index=index,
                        field_name=attr_multi_def.field_name,
                        value=multi_val,
                        importer_name=config.DRUG_IMPORTER_PLUGIN,
                    )
                )
        # attrs_multi_ref
        for attr_multi_ref_create in drug_create.attrs_multi_ref:
            attr_multi_ref_def = find_attr_def(
                "attrs_multi_ref", attr_multi_ref_create.field_name
            )
            if attr_multi_ref_create.values is None:
                continue
            for index, multi_val in enumerate(attr_multi_ref_create.values):
                lov_item = await find_lov_item(
                    "attrs_multi_ref", attr_multi_ref_def.field_name, multi_val
                )
                drug.attrs_multi_ref.append(
                    DrugValMultiRef(
                        value_index=index,
                        field_name=attr_multi_ref_def.field_name,
                        value=multi_val,
                        importer_name=config.DRUG_IMPORTER_PLUGIN,
                        # lov_item=lov_item,
                    )
                )

        # codes - drug code attr (e.g. atc code,pzn,...)
        code_defs = await drug_importer.get_code_definitions()
        if drug_create.codes is not None:

            for code_create in drug_create.codes:
                code_create: DrugCodeApi = code_create
                code_system: DrugCodeSystem = next(
                    (ad for ad in code_defs if ad.id == code_create.code_system_id),
                    None,
                )
                if code_system is None:
                    raise CustomDrugAttrNotValid(
                        f"Custom drug code system name '{code_create.code_system_id}' is not a availabe code system in the current drug dataset. Can not create custom drug."
                    )
                if code_system.unique:
                    existing_code_query = (
                        select(DrugCode)
                        .where(DrugCode.code_system_id == code_system.id)
                        .where(DrugCode.code == code_create.code)
                        .limit(1)
                    )
                    existing_code_res = await self.session.exec(existing_code_query)
                    existing_code = existing_code_res.one_or_none()
                    if existing_code is not None:
                        raise DrugWithCodeAllreadyExists(
                            f"A drug with the code '{code_system.id}':'{code_create.code}' allready exists (Drug.id: '{existing_code.drug_id}')"
                        )
                new_drug_code = DrugCode(
                    code_system_id=code_system.id, code=code_create.code
                )
                new_objects.append(new_drug_code)
                drug.codes.append(new_drug_code)
        new_objects.append(drug)
        self.session.add_all(new_objects)
        await self.session.commit()
        # await self.session.refresh(drug)
        drug: DrugData = await self.get(
            drug.id,
            raise_exception_if_none=ValueError("COULD NOT FIND DRUG IN DATABASE"),
        )
        return drug
