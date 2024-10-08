from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any, Literal
import uuid
from functools import partial
from pydantic import BaseModel

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


class TypCastingInfo(BaseModel):
    python_type: Callable
    casting_func: Callable


class ValueTypeCasting(enum.Enum):
    STR = TypCastingInfo(python_type=str, casting_func=str)
    INT = TypCastingInfo(python_type=int, casting_func=int)
    FLOAT = TypCastingInfo(python_type=float, casting_func=float)
    BOOL = TypCastingInfo(python_type=bool, casting_func=bool)
    DATETIME = TypCastingInfo(
        python_type=datetime.datetime, casting_func=datetime.datetime.fromisoformat
    )
    DATE = TypCastingInfo(
        python_type=datetime.date, casting_func=datetime.date.fromisoformat
    )


class CustomPreParserFunc(enum.Enum):
    # partial wrapper because plain function wont work as enum values
    # see https://stackoverflow.com/a/40339397/12438690
    WIDO_GKV_DATE = partial(
        lambda x: datetime.datetime.strptime(x, "%Y%m%d").date().isoformat()
    )


class DrugAttrFieldDefinitionAPIRead(DrugModelTableBase, table=False):
    field_name: str = Field(primary_key=True)
    field_name_display: str = Field(
        description="The title of the field for displaying humans"
    )
    field_desc: Optional[str] = Field(
        default=None, description="Helptext about the content of the field"
    )
    optional: bool = False
    default: Optional[str] = None
    has_list_of_values: bool = Field(default=False)
    type: Literal[tuple([e.name for e in ValueTypeCasting])] = Field(
        default=ValueTypeCasting.STR.name,
        description="The type of this value gets casted into, by the backend, as before its passing the RestAPI",
    )


class DrugAttrFieldDefinition(DrugAttrFieldDefinitionAPIRead, table=True):
    __tablename__ = "drug_attr_field_definition"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields"
    }
    importer_name: str = Field(
        primary_key=True,
        description="A field definiton always comes from one drug data importer. We may have multiple importers in the lifecycle of the application, therefore we need to distinguish the fields per drug data importer.",
    )
    type: ValueTypeCasting = Field(
        default=ValueTypeCasting.STR,
        description="The type of this value gets casted into, as before its passing the RestAPI",
    )
    default: Optional[str]
    searchable: bool = Field(
        default=False,
        description="If this field is will be take into account while using /drug/search endpoint.",
    )
    pre_parser: Optional[CustomPreParserFunc] = Field(
        default=None,
        description="Function that can transform the input value into a fitting string",
    )
    examples: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    list_of_values: List["DrugAttrFieldLovItem"] = Relationship(back_populates="field")