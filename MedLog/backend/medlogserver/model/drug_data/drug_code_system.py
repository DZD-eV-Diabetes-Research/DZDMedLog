from typing import List, Self, Optional
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import DrugModelTableBase


class DrugCodeSystem(DrugModelTableBase, table=True):
    __tablename__ = "drug_code_system"
    __table_args__ = {
        "comment": "A list of national pharmaceutical product indexes. To be completed..."
    }

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
