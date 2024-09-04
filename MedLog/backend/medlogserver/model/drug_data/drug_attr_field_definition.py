from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any
import uuid
from sqlmodel import Field, SQLModel, Relationship, JSON
from pydantic_core import PydanticUndefined
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from dataclasses import dataclass
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)


if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug_attr_field_lov_item import (
        DrugAttrFieldLovItem,
    )
from enum import Enum


@dataclass
class TypCastingInfo:
    python_type: Type
    casting_func: Callable


class ValueTypeCasting(Enum):
    STR = TypCastingInfo(str, str)
    INT = TypCastingInfo(int, int)
    FLOAT = TypCastingInfo(float, float)
    DATETIME = TypCastingInfo(datetime.datetime, datetime.datetime.fromisoformat)
    DATE = TypCastingInfo(datetime.date, datetime.date.fromisoformat)


from typing import NamedTuple


class DrugAttrFieldDefinition(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field_definition"
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
    type: ValueTypeCasting = Field(
        default=ValueTypeCasting.STR,
        description="The type of this value gets casted into, as before its passing the RestAPI",
    )
    examples: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    list_of_values: List["DrugAttrFieldLovItem"] = Relationship(back_populates="field")
