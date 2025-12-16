from typing import List, Self, Optional
import uuid
from sqlmodel import Field, SQLModel, UniqueConstraint
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import DrugModelTableBase


class DrugCodeSystem(DrugModelTableBase, table=True):
    __tablename__ = "drug_code_system"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "importer_name",
            name="uq_code_system_field_definition__field__importer",
        ),
        UniqueConstraint(
            "id",
            "importer_name",
            name="uq_code_system_field_definition_id__field__importer",
        ),
        {
            "comment": "Definition of dataset specific fields and lookup fields. this is a read only table. The attribute field definitons are defined in code. Any changes on the SQL table rows/values will be overwriten."
        },
    )
    id: str = Field(
        description="Shortname identifier for the national mmedication code system. Also the name for one code instance.",
        sa_type=String,
        primary_key=True,
        schema_extra={"examples": ["PZN", "NDC"]},
    )
    name: str = Field(
        description="Longname identifier for the national drug code system.",
        sa_type=String,
        schema_extra={"examples": ["Pharmazentralnummer", "National Drug Code"]},
    )
    country: str = Field(
        description="Country that uses this system",
        sa_type=String,
        schema_extra={"examples": ["Germany", "USA"]},
    )
    desc: Optional[str] = Field(
        default=None, description="Information about the code system"
    )
    optional: bool = Field(
        default=False,
        description="Will every drug have such code or is it optional? This can be important when referencing drugs as we can only guarante a reference via code if it is non optional.",
    )
    unique: bool = Field(
        default=True,
        description="Will every drug have a unique code or can multiple drug products can have the same code.",
    )

    code_icon: Optional[str] = Field(
        default=None,
        description="A unicode icon that can be shown next to the code field or instead of the `name`",
        schema_extra={"examples": ["💩", "🔢", "💊"]},
    )
    code_display_sort_order: Optional[int] = Field(
        default=0,
        description="This should define the sequence how the code fields are listed in the client `0` should be the first field(s). The higher the number, the farther down the field should appear.",
    )
    client_visible: bool = Field(
        default=True,
        description="Should the code be shown in the UI. Some IDs are internal and are not interesting for the client.",
    )
    importer_name: str = Field()
