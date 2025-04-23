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
        ForeignKeyConstraint(
            ["importer_name", "field_name"],
            [
                "drug_attr_field_definition.importer_name",
                "drug_attr_field_definition.field_name",
            ],
            name="fk_lovitem_fielddef",
        ),
        {"comment": "Attr fields lists of values"},
    )
    field_name: str = Field(
        foreign_key="drug_attr_field_definition.field_name", primary_key=True
    )
    importer_name: str = Field(
        foreign_key="drug_attr_field_definition.importer_name", primary_key=True
    )
    value: str = Field(primary_key=True)
    display: str = Field()
    sort_order: Optional[int] = Field(default=0)
    field_definition: DrugAttrFieldDefinition = Relationship(
        sa_relationship=RelationshipProperty(
            "DrugAttrFieldDefinition",
            foreign_keys="[DrugAttrFieldLovItem.importer_name,DrugAttrFieldLovItem.field_name]",
            primaryjoin="and_(DrugAttrFieldLovItem.importer_name==DrugAttrFieldDefinition.importer_name, DrugAttrFieldLovItem.field_name==DrugAttrFieldDefinition.field_name)",
            back_populates="list_of_values",
        ),
    )
