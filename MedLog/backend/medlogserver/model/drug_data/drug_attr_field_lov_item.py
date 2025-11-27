from typing import List, Self, Optional
import uuid
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    UniqueConstraint,
    ForeignKeyConstraint,
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
        UniqueConstraint(
            "importer_name",
            "field_name",
            "drug_dataset_version_fk",
            name="unique_lovitem_fielddef",
            deferrable=True,  # Only PostgreSQL will respect this
            initially="IMMEDIATE",
        ),
        {"comment": "Attr fields lists of values"},
    )
    field_name: str = Field(primary_key=True)
    importer_name: str = Field(primary_key=True)
    value: str = Field(primary_key=True)
    display: str = Field()
    sort_order: Optional[int] = Field(default=0)
    drug_dataset_version_fk: uuid.UUID = Field(
        foreign_key="drug_dataset_version.id", primary_key=True
    )
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    """
