from typing import List, Self, Optional
import uuid
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    UniqueConstraint,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
)
from sqlalchemy import String, Integer, Column, SmallInteger
from sqlalchemy.orm.relationships import RelationshipProperty
from medlogserver.model.drug_data.drug_dataset_version import (
    DrugDataSetVersion,
)
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)


class DrugAttrFieldLovItemCREATE(SQLModel):
    value: str = Field()
    display: str = Field()
    sort_order: Optional[int] = Field(default=0)


class DrugAttrFieldLovItemAPIRead(DrugAttrFieldLovItemCREATE):
    pass


class DrugAttrFieldLovItem(DrugModelTableBase, DrugAttrFieldLovItemAPIRead, table=True):
    __tablename__ = "drug_attr_field_lov_item"
    __table_args__ = (
        PrimaryKeyConstraint(
            "field_name", "importer_name", "value", "drug_dataset_version_fk"
        ),
        {"comment": "Attr fields lists of values"},
    )
    field_name: str = Field(foreign_key="drug_attr_field_definition.field_name")
    importer_name: str = Field()
    value: str = Field()
    display: str = Field()
    sort_order: Optional[int] = Field(default=0)
    drug_dataset_version_fk: uuid.UUID = Field(foreign_key="drug_dataset_version.id")
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    """
