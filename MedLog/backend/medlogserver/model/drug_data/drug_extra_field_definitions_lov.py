from typing import List, Self, Optional
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_extra_field_definitions import (
    DrugExtraFieldDefinition,
)


class DrugExtraFieldDefinitionLOV(DrugModelTableBase, table=True):
    __tablename__ = "drug_extra_field_definitions_lovs"
    __table_args__ = {"comment": "Extra fields lists of values"}
    field_name: str = Field(foreign_key="drug_extra_field_definitions.field_name")
    field: DrugExtraFieldDefinition = Relationship(back_populates="list_of_values")
    key: str = Field(primary_key=True)
    display_value: str = Field()
    sort_order: Optional[int] = Field(default=0)
