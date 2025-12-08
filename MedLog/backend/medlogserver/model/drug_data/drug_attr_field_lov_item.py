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
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_ref_val_field_def",
            columns=["field_name", "importer_name"],
            refcolumns=[
                "drug_attr_field_definition.field_name",
                "drug_attr_field_definition.importer_name",
            ],
            deferrable=True,  # Only PostgreSQL will respect this
            initially="IMMEDIATE",
        ),
        {"comment": "Attr fields lists of values"},
    )
    field_name: str = Field(primary_key=True)
    importer_name: str = Field(primary_key=True)
    value: str = Field()
    display: str = Field()
    sort_order: Optional[int] = Field(default=0)
    drug_dataset_version_fk: uuid.UUID = Field(foreign_key="drug_dataset_version.id")
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    """
