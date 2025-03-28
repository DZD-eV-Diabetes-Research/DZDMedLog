from typing import List, Self, Optional, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship, ForeignKeyConstraint, JSON
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
    from medlogserver.model.drug_data.drug import DrugData


class DrugValApiCreate(DrugModelTableBase, table=False):
    field_name: str = Field(
        primary_key=True,
        foreign_key="Name of the attribute. Available field_names can be retrieved from REST API Endpoint '/v2/drug/field_def' ",
    )
    value: Optional[str] = Field(
        default=None,
        description="Value of the drug attribute",
    )


class DrugMultiValApiCreate(DrugModelTableBase, table=False):
    field_name: str = Field(
        primary_key=True,
        foreign_key="Name of the attribute. Available field_names can be retrieved from REST API Endpoint '/v2/drug/field_def' ",
    )
    values: Optional[List[str]] = Field(
        default=None,
        description="Value of the drug attribute",
    )


class DrugVal(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_val"

    drug_id: uuid.UUID = Field(foreign_key="drug.id", primary_key=True)
    field_name: str = Field(
        primary_key=True, foreign_key="drug_attr_field_definition.field_name"
    )
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    field_definition: DrugAttrFieldDefinition = Relationship()
    drug: "DrugData" = Relationship(back_populates="attrs")


class DrugValRef(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_ref_val"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_ref_value_obj",
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
    lov_item: DrugAttrFieldLovItem = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    drug: "DrugData" = Relationship(back_populates="attrs_ref")


class DrugValMulti(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_multi_val"

    drug_id: uuid.UUID = Field(foreign_key="drug.id", primary_key=True)
    field_name: str = Field(
        primary_key=True, foreign_key="drug_attr_field_definition.field_name"
    )
    value_index: int = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of multiple value as list of string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    field_definition: DrugAttrFieldDefinition = Relationship()
    drug: "DrugData" = Relationship(back_populates="attrs_multi")


class DrugValMultiRef(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_multi_ref_val"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_ref_value_obj",
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
    value_index: int = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of multiple reference value as list of string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )

    field_definition: DrugAttrFieldDefinition = Relationship()
    lov_item: DrugAttrFieldLovItem = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    drug: "DrugData" = Relationship(back_populates="attrs_multi_ref")


from pydantic import BaseModel


class DrugAttrRefApiRead(BaseModel):
    value: str | int | float | bool
    display: str
    ref_list_path: str
