from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any, Literal
import uuid
from functools import partial
from pydantic import BaseModel, field_validator, model_validator

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


class DrugAttrFieldDefinitionAPIReadBase(DrugModelTableBase):
    pass


class DrugAttrFieldDefinitionAPIRead(DrugAttrFieldDefinitionAPIReadBase, table=False):
    field_name: str = Field(primary_key=True)
    field_name_display: str = Field(
        description="The title of the field for displaying humans"
    )
    field_desc: Optional[str] = Field(
        default=None,
        description="Helptext for users about the content of the field. For internal documenation purposes see 'desc'",
    )
    optional: bool = False
    default: Optional[str] = None
    is_reference_list_field: bool = Field(
        default=False,
        description="If true each value has a reference list with a display value. Values that are not in the reference list are not allowed. e.g. A drug can only be 'freely-available','pharmacy-only' or 'prescription-only'",
    )
    is_multi_val_field: bool = Field(
        default=False,
        description="If true this field can hold a list of values instead of a single one. E.g. A drug can have a list of keywords.",
    )
    type: Literal[tuple([e.name for e in ValueTypeCasting])] = Field(
        default=ValueTypeCasting.STR.name,
        description="The type of this value gets casted into, by the backend, as before its passing the RestAPI",
    )
    show_in_search_results: bool = Field(
        default=True,
        description="Should this Field be shown in search results. This is just an instruction field for the UI and has effect on the backend.",
    )
    used_for_custom_drug: bool = Field(
        default=True,
        description="When creating a custom drug, should this field be used for the form in the UI. Atm this field is only an instruction field for the UI and is not validated.",
    )


class DrugAttrRefFieldDefinitionAPIRead(DrugAttrFieldDefinitionAPIRead, table=False):
    ref_list: str = Field(
        default=None, description="API Path to the reference list values"
    )
    is_reference_list_field: bool = Field(
        default=True,
        description="If true each value has a reference list with a display value. Values that are not in the reference list are not allowed. e.g. A drug can only be 'freely-available','pharmacy-only' or 'prescription-only'",
    )

    @model_validator(mode="after")
    def _gen_ref_list_path(self: Self) -> Self:
        self.ref_list = f"/v2/drug/field_def/{self.field_name}/refs"
        return self


class DrugAttrMultiFieldDefinitionAPIRead(DrugAttrFieldDefinitionAPIRead, table=False):
    is_multi_val_field: bool = Field(
        default=True,
        description="If true this field can hold a list of values instead of a single one. E.g. A drug can have a list of keywords.",
    )
    type: Literal[tuple([e.name for e in ValueTypeCasting])] = Field(
        default=f"List[{ValueTypeCasting.STR.name}]",
        description="The type of this value gets casted into, by the backend, as before its passing the RestAPI",
    )


class DrugAttrMultiRefFieldDefinitionAPIRead(
    DrugAttrRefFieldDefinitionAPIRead, table=False
):
    ref_list: str = Field(
        default=None, description="API Path to the reference list values"
    )
    is_reference_list_field: bool = Field(
        default=True,
        description="If true each value has a reference list with a display value. Values that are not in the reference list are not allowed. e.g. A drug can only be 'freely-available','pharmacy-only' or 'prescription-only'",
    )
    is_multi_val_field: bool = Field(
        default=True,
        description="If true this field can hold a list of values instead of a single one. E.g. A drug can have a list of keywords.",
    )


class DrugAttrFieldDefinition(DrugAttrFieldDefinitionAPIRead, table=True):
    __tablename__ = "drug_attr_field_definition"
    __table_args__ = {
        "comment": "Definition of dataset specific fields and lookup fields. this is a read only table. The attribute field definitons are defined in code. Any changes on the SQL table rows/values will be overwriten."
    }
    desc: Optional[str] = Field(
        default=None,
        description="Describe what is in the field. For internal documenation purposes. For user helptext see 'field_desc'",
    )
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
