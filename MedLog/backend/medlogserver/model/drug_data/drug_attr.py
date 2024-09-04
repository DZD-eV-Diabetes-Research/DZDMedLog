from typing import List, Self, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship, ForeignKeyConstraint
from sqlalchemy import String, Integer, Column, SmallInteger
import datetime
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)

if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug import Drug


class DrugAttr(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_field"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_sondercode_bedeutung",
            columns=["field_name", "value"],
            refcolumns=[
                "drug_attr_field_lov_item.field_name",
                "drug_attr_field_lov_item.value",
            ],
        ),
        {"comment": "Definition of dataset specific fields and lookup fields"},
    )

    drug_id: uuid.UUID = Field(foreign_key="drug.id", primary_key=True)
    field_name: str = Field(
        primary_key=True, foreign_key="drug_attr_field_definition.field_name"
    )
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    field_definition: DrugAttrFieldDefinition = Relationship()
    lov_entry: Optional[DrugAttrFieldLovItem] = Relationship()
    drug: "Drug" = Relationship(back_populates="attrs")
