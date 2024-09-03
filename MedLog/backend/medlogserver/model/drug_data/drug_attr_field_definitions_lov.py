from typing import List, Self, Optional
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_attr_field_definitions import (
    DrugAttrFieldDefinition,
)


class DrugAttrFieldDefinitionLovItem(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field_definitions_lovs"
    __table_args__ = {"comment": "Attr fields lists of values"}
    field_name: str = Field(
        foreign_key="drug_attr_field_definitions.field_name", primary_key=True
    )
    value: str = Field(primary_key=True)
    display_value: str = Field()
    sort_order: Optional[int] = Field(default=0)
    field: DrugAttrFieldDefinition = Relationship(back_populates="list_of_values")
