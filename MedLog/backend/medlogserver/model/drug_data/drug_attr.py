from typing import List, Self, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)

if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug import Drug


class DrugAttr(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields"
    }
    drug_id: uuid.UUID = Field(foreign_key="drug.id")
    field_name: str = Field(
        primary_key=True, foreign_key="drug_attr_field_definition.field_name"
    )
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    field_definition: DrugAttrFieldDefinition = Relationship()
    drug: "Drug" = Relationship(back_populates="attrs")
