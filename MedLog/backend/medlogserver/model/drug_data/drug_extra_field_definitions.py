from typing import List, Self, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)

if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug_extra_field_definitions_lov import (
        DrugExtraFieldDefinitionLOV,
    )
from enum import Enum


class ValueCastingFunc(str, Enum):
    INT = int
    FLOAT = float
    DATETIME = datetime.datetime.fromisoformat
    DATE = datetime.date.fromisoformat


class DrugExtraFieldDefinition(DrugModelTableBase, table=True):
    __tablename__ = "drug_extra_field_definitions"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields"
    }
    field_name: str = Field(primary_key=True)
    has_list_of_values: bool = Field(default=False)
    type: Optional[ValueCastingFunc] = Field(default=None)
    list_of_values: List["DrugExtraFieldDefinitionLOV"] = Relationship(
        back_populates="field"
    )
