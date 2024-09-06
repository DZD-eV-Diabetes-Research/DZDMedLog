from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any
import uuid
from functools import partial


from sqlmodel import Field, SQLModel, Relationship, JSON, Enum, Column
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
import enum


@dataclass
class TypCastingInfo:
    python_type: Type
    casting_func: Callable


class ValueTypeCasting(enum.Enum):
    STR = TypCastingInfo(str, str)
    INT = TypCastingInfo(int, int)
    FLOAT = TypCastingInfo(float, float)
    DATETIME = TypCastingInfo(datetime.datetime, datetime.datetime.fromisoformat)
    DATE = TypCastingInfo(datetime.date, datetime.date.fromisoformat)


class CustomPreParserFunc(enum.Enum):
    # partial wrapper because plain function wont work as enum values
    # see https://stackoverflow.com/a/40339397/12438690
    WIDO_GKV_DATE = partial(
        lambda x: datetime.datetime.strptime(x, "%Y%m%d").date().isoformat()
    )


class DrugAttrFieldDefinition(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field_definition"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields"
    }
    field_name: str = Field(primary_key=True)
    field_display: str = Field(
        description="The title of the field for displaying humans"
    )
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
    pre_parser: Optional[CustomPreParserFunc] = Field(
        default=None,
        description="Function that can transform the input value into a fitting string",
    )
    examples: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    list_of_values: List["DrugAttrFieldLovItem"] = Relationship(back_populates="field")
