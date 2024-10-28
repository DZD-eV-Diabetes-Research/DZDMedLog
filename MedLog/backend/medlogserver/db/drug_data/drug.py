from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated, Tuple
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
from medlogserver.model.drug_data.drug import Drug
from medlogserver.db._base_crud import create_crud_base
from medlogserver.db.interview import Interview
from medlogserver.api.paginator import QueryParamsInterface
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.drug_attr import (
    DrugRefAttr,
    DrugAttr,
    DrugAttrApiCreate,
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


class CustomDrugAttrNotValid(Exception):
    pass


class DrugWithCodeAllreadyExists(Exception):
    pass


class DrugCRUD(
    create_crud_base(
        table_model=Drug,
        read_model=Drug,
        create_model=Drug,
        update_model=Drug,
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
                Drug.source_dataset_id == sub_query,
                Drug.source_dataset_id == sub_query_custom_drugs,
            )
        )
        return query

    async def count(
        self,
    ) -> int:
        query = select(func.count()).select_from(Drug)
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )
        results = await self.session.exec(statement=query)
        return results.first()

    async def list(
        self,
        filter_study_id: UUID = None,
        hide_completed: bool = False,
        pagination: QueryParamsInterface = None,
        include_relations: bool = False,
    ) -> Sequence[Drug]:
        if isinstance(filter_study_id, str):
            filter_study_id: UUID = UUID(filter_study_id)
        # log.info(f"Event.Config.order_by {Event.Config.order_by}")
        query = select(Drug)
        if include_relations:
            query = query.options(
                selectinload(Drug.attrs),
                selectinload(Drug.ref_attrs).selectinload(DrugRefAttr.lov_item),
                selectinload(Drug.codes),
            )
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )
        if pagination:
            query = pagination.append_to_query(query)
        results = await self.session.exec(statement=query)
        return results.all()

    async def get_multiple(
        self,
        ids: List[str],
        pagination: QueryParamsInterface = None,
        keep_result_in_ids_order: bool = True,
    ) -> Sequence[Drug]:
        query = select(Drug).where(col(Drug.id).in_(ids))
        query = await self.append_current_and_custom_drugs_dataset_version_where_clause(
            query
        )

        if pagination:
            query = pagination.append_to_query(query)

        results = await self.session.exec(statement=query)
        if keep_result_in_ids_order:
            # todo: maybe we can solve the drug order in sql?
            db_order: List[Drug] = results.all()
            new_order: List[Drug] = []
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
    ) -> Drug:
        drug_importer_class = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]
        drug_importer = drug_importer_class()

        new_objects = []
        new_drug_id = uuid.uuid4()

        drug = Drug(
            id=new_drug_id,
            source_dataset_id=custom_drug_dataset.id,
            is_custom_drug=True,
            **drug_create.model_dump(exclude=["attrs", "ref_attrs", "codes"]),
        )
        new_objects.append(drug)

        attr_defs = await drug_importer.get_attr_field_definitions()
        for attr_create in drug_create.attrs:
            attr_def: DrugAttrFieldDefinition = next(
                (ad for ad in attr_defs if ad.field_name == attr_create.field_name),
                None,
            )
            if attr_def is None:
                raise CustomDrugAttrNotValid(
                    f"Attribute with name '{attr_create.field_name}' is not supported in current drug dataset. Can not create custom drug."
                )
            new_attr = DrugAttr(
                drug_id=drug.id, field_name=attr_def.field_name, value=attr_create.value
            )
            new_objects.append(new_attr)
            drug.attrs.append(new_attr)

        ref_attr_defs = await drug_importer.get_ref_attr_field_definitions()
        for ref_attr_create in drug_create.ref_attrs:
            ref_attr_def: DrugAttrFieldDefinition = next(
                (
                    ad
                    for ad in ref_attr_defs
                    if ad.field_name == ref_attr_create.field_name
                ),
                None,
            )
            if ref_attr_def is None:
                raise CustomDrugAttrNotValid(
                    f"Attribute with name '{ref_attr_create.field_name}' is not supported in current drug dataset. Can not create custom drug."
                )
            lov_item_query = select(DrugAttrFieldLovItem).where(
                and_(
                    DrugAttrFieldLovItem.field_name == ref_attr_def.field_name,
                    DrugAttrFieldLovItem.value == ref_attr_create.value,
                )
            )
            lov_item_res = await self.session.exec(lov_item_query)
            lov_item = lov_item_res.one_or_none()
            print("lov_item", lov_item)
            if lov_item is None:
                raise CustomDrugAttrNotValid(
                    f"Value '{ref_attr_create.value}' for ref/select attr with name '{ref_attr_create.field_name}' is not a valid selection. Can not create custom drug."
                )
            log.debug(("lov_item", type(lov_item), lov_item))
            new_attr = DrugRefAttr(
                drug_id=drug.id,
                field_name=ref_attr_def.field_name,
                value=ref_attr_create.value,
                lov_item=lov_item,
            )
            new_objects.append(new_attr)
            drug.ref_attrs.append(new_attr)
        code_defs = await drug_importer.get_code_definitions()
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
                print("code_create.code", code_create.code)
                existing_code_query = (
                    select(DrugCode)
                    .where(DrugCode.code_system_id == code_system.id)
                    .where(DrugCode.code == code_create.code)
                    .limit(1)
                )
                existing_code_res = await self.session.exec(existing_code_query)
                existing_code = existing_code_res.one_or_none()
                print("existing_code", existing_code)
                if existing_code is not None:
                    raise DrugWithCodeAllreadyExists(
                        f"A drug with the code '{code_system.id}':'{code_create.code}' allready exists (Drug.id: '{existing_code.drug_id}')"
                    )
            new_drug_code = DrugCode(
                code_system_id=code_system.id, code=code_create.code
            )
            new_objects.append(new_drug_code)
            drug.codes.append(new_drug_code)
        self.session.add_all(new_objects)
        await self.session.commit()
        # await self.session.refresh(drug)
        return drug
        ## YOU ARE HERE: get attr defintions, validate input, save to new_obnjects

        # save all objects to db, return drug
