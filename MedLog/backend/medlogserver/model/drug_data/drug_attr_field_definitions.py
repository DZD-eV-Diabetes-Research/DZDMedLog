from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any
import uuid
from sqlmodel import Field, SQLModel, Relationship
from pydantic_core import PydanticUndefined
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from dataclasses import dataclass
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)


if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug_attr_field_definitions_lov import (
        DrugAttrFieldDefinitionLovItem,
    )
from enum import Enum


@dataclass
class TypCastingInfo:
    python_type: Type
    casting_func: Callable


class ValueTypeCasting(str, Enum):
    INT = TypCastingInfo(int, int)
    FLOAT = TypCastingInfo(float, float)
    DATETIME = TypCastingInfo(datetime.datetime, datetime.datetime.fromisoformat)
    DATE = TypCastingInfo(datetime.date, datetime.date.fromisoformat)


class DrugAttrFieldDefinition(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field_definitions"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields"
    }
    field_name: str = Field(primary_key=True)
    field_desc: Optional[str] = Field(
        default=None, description="Helptext about the content of the field"
    )
    optional: bool = False
    default: Optional[str]
    has_list_of_values: bool = Field(default=False)
    type: Optional[ValueTypeCasting] = Field(
        default=None, description="'None' means 'is a string'"
    )
    list_of_values: List["DrugAttrFieldDefinitionLovItem"] = Relationship(
        back_populates="field"
    )
