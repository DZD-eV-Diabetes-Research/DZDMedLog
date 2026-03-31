from typing import List, Self, Optional, TYPE_CHECKING, Type, Callable, Any, Literal
import uuid
from functools import partial
from pydantic import (
    BaseModel,
    field_validator,
    model_validator,
    field_serializer,
)

from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, SQLModel, Relationship, JSON, Enum, Column, UniqueConstraint
from pydantic_core import PydanticUndefined
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from dataclasses import dataclass
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model._utils import SqlStringListText, SqlStringListAny


if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug_attr_field_lov_item import (
        DrugAttrFieldLovItem,
    )
import enum
from medlogserver.model.unset import Unset
from medlogserver.log import get_logger

log = get_logger()


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


ValueTypeCastingNames = tuple([e.name for e in ValueTypeCasting])


class DisplayPriorityClass(enum.IntEnum):
    CLASS1 = 1
    CLASS2 = 2
    CLASS3 = 3


class CustomPreParserFunc(enum.Enum):
    WIDO_GKV_DATE = enum.member(
        lambda x: datetime.datetime.strptime(x, "%Y%m%d").date().isoformat()
    )


CustomPreParserFuncNames = tuple([e.name for e in CustomPreParserFunc])


class DrugAttrFieldDefinitionAPIReadBase(DrugModelTableBase):
    pass


class DrugAttrFieldDefinitionAPIRead(DrugAttrFieldDefinitionAPIReadBase, table=False):
    field_name: str = Field(primary_key=True)
    field_name_display: str = Field(
        description="The title of the field for displaying humans"
    )
    field_display_priority_class: DisplayPriorityClass = Field(
        default=DisplayPriorityClass.CLASS3,
        description="A hint on how important this field is for displaying the user. E.g. a class 1 field should be immediately visible to the user on drug search to help identify the drug. A class 3 field is ok to be visible after clicking on some `more info...`-button",
    )

    field_desc: Optional[str] = Field(
        default=None,
        description="Helptext for users about the content of the field. For internal documenation purposes see 'desc'",
    )
    field_icon: Optional[str] = Field(
        default=None,
        description="A unicode icon that can be shown next to the field or instead of the `field_name_display`",
        schema_extra={"examples": ["💩", "🔢", "💊"]},
    )
    field_display_sort_order: Optional[int] = Field(
        default=0,
        description="This should define the sequence how fields are listed in the client in a particular `field_display_priority_class`. `0` should be the first field(s). The higher the number, the farther down the field should appear.",
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
    value_type: Literal[ValueTypeCastingNames] = Field(
        default=ValueTypeCasting.STR.name,
        description="The type of this value gets casted into, by the backend, as before its passing the RestAPI",
        sa_column=Column(
            Enum(
                ValueTypeCastingNames,
                name="valuetypecasting",
            ),
            nullable=False,
        ),
    )
    show_in_search_results: bool = Field(
        default=True,
        description="Should this Field be shown in search results. This is just an instruction field for the UI and has effect on the backend.",
    )
    used_for_custom_drug: bool = Field(
        default=True,
        description="When creating a custom drug, should this field be used for the form in the UI. Atm this field is only an instruction field for the UI and is not validated.",
    )
    is_large_reference_list: bool = Field(
        default=False,
        description="Just an Info for the client that this list contains many items. The client could use that to lazy laod or/and offer a search-select field.",
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
        self.ref_list = f"/api/drug/field_def/{self.field_name}/refs"
        return self


class DrugAttrMultiFieldDefinitionAPIRead(DrugAttrFieldDefinitionAPIRead, table=False):
    is_multi_val_field: bool = Field(
        default=True,
        description="If true this field can hold a list of values instead of a single one. E.g. A drug can have a list of keywords.",
    )
    value_type: Literal[ValueTypeCastingNames] = Field(
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
    __table_args__ = (
        UniqueConstraint(
            "field_name",
            "importer_name",
            name="uq_drug_attr_field_definition__field__importer",
        ),
        {
            "comment": "Definition of dataset specific fields and lookup fields. this is a read only table. The attribute field definitons are defined in code. Any changes on the SQL table rows/values will be overwriten."
        },
    )

    def __init__(self, **data):
        if data.get("default") == Unset:
            data["default"] = "<Unset>"
        super().__init__(**data)

    field_name: str = Field(primary_key=True)
    desc: Optional[str] = Field(
        default=None,
        description="Describe what is in the field. For internal documenation purposes. For user helptext see 'field_desc'",
    )
    importer_name: str = Field(
        primary_key=True,
        description="A field definiton always comes from one drug data importer. We may have multiple importers in the lifecycle of the application, therefore we need to distinguish the fields per drug data importer.",
    )
    value_type: ValueTypeCasting = Field(
        default=ValueTypeCasting.STR,
        description="The type of this value gets casted into, as before its passing the RestAPI",
    )
    has_default: bool = Field(
        default=False,
        description=(
            "Indicates whether a default value is explicitly defined for this field. "
            "If False, no default is set and the field is considered unset."
        ),
    )
    default: Optional[str] = Field(
        default=None,
        description=(
            "The default value to use when no input is provided. "
            "Only applies if 'has_default' is True. "
            "If this is None and 'has_default' is True, it means the default is explicitly set to null/empty."
        ),
    )

    searchable: bool = Field(
        default=False,
        description="If this field is will be take into account while using /drug/search endpoint.",
    )
    pre_parser: str | None = Field(
        default=None,
        description="Function that can transform the input value into a fitting string. Function must be registered in CustomPreParserFunc",
    )
    examples: List[str] = Field(
        default_factory=list, sa_column=Column(SqlStringListAny)
    )
