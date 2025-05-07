from typing import List, Self, Optional, TYPE_CHECKING
import uuid
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    ForeignKeyConstraint,
    JSON,
)
from sqlalchemy.orm import RelationshipProperty
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
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_val_field_def",
            columns=["field_name", "importer_name"],
            refcolumns=[
                "drug_attr_field_definition.field_name",
                "drug_attr_field_definition.importer_name",
            ],
            initially="DEFERRED",
        ),
        {"comment": "Actual attribute value for a drug"},
    )
    drug_id: uuid.UUID = Field(
        foreign_key="drug.id", primary_key=True, ondelete="CASCADE"
    )
    field_name: str = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    importer_name: str = Field()
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    
    field_definition: DrugAttrFieldDefinition = Relationship(
        sa_relationship=RelationshipProperty(
            "DrugAttrFieldDefinition",
            foreign_keys="[DrugVal.importer_name,DrugVal.field_name]",
            primaryjoin="and_(DrugVal.importer_name==DrugAttrFieldDefinition.importer_name, DrugVal.field_name==DrugAttrFieldDefinition.field_name)",
            # back_populates="list_of_values",
        ),
    )
    """
    drug: "DrugData" = Relationship(back_populates="attrs")


class DrugValRef(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_ref_val"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_ref_val__lov_item",
            columns=["field_name", "value", "importer_name"],
            refcolumns=[
                "drug_attr_field_lov_item.field_name",
                "drug_attr_field_lov_item.value",
                "drug_attr_field_lov_item.importer_name",
            ],
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_ref_val_field_def",
            columns=["field_name", "importer_name"],
            refcolumns=[
                "drug_attr_field_definition.field_name",
                "drug_attr_field_definition.importer_name",
            ],
            initially="DEFERRED",
        ),
        {"comment": "Definition of dataset specific fields and lookup fields"},
    )

    drug_id: uuid.UUID = Field(
        foreign_key="drug.id", primary_key=True, ondelete="CASCADE"
    )
    field_name: str = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    importer_name: str = Field()
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    """
    lov_item: DrugAttrFieldLovItem = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "primaryjoin": (
                "and_("
                "foreign(DrugValRef.field_name) == remote(DrugAttrFieldLovItem.field_name), "
                "foreign(DrugValRef.importer_name) == remote(DrugAttrFieldLovItem.importer_name), "
                "foreign(DrugValRef.value) == remote(DrugAttrFieldLovItem.value)"
                ")"  # ToDo: idk why i need this funky primaryjoin thingy here :(
            ),
        }
    )

    drug: "DrugData" = Relationship(back_populates="attrs_ref")


class DrugValMulti(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_multi_val"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_multi_val_field_def",
            columns=["field_name", "importer_name"],
            refcolumns=[
                "drug_attr_field_definition.field_name",
                "drug_attr_field_definition.importer_name",
            ],
            initially="DEFERRED",
        ),
        {"comment": "Actual single value of a multi/list attribute  for a drug"},
    )
    drug_id: uuid.UUID = Field(
        foreign_key="drug.id", primary_key=True, ondelete="CASCADE"
    )
    field_name: str = Field(primary_key=True)
    value_index: int = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of multiple value as list of string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    importer_name: str = Field()
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    
    field_definition: DrugAttrFieldDefinition = Relationship(
        sa_relationship=RelationshipProperty(
            "DrugAttrFieldDefinition",
            foreign_keys="[DrugValMulti.importer_name,DrugValMulti.field_name]",
            primaryjoin="and_(DrugValMulti.importer_name==DrugAttrFieldDefinition.importer_name, DrugValMulti.field_name==DrugAttrFieldDefinition.field_name)",
            # back_populates="list_of_values",
        ),
    )
    """
    drug: "DrugData" = Relationship(back_populates="attrs_multi")


class DrugValMultiRef(DrugModelTableBase, table=True):
    __tablename__ = "drug_attr_multi_ref_val"
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_multi_ref_val__lov_item",
            columns=["field_name", "value", "importer_name"],
            refcolumns=[
                "drug_attr_field_lov_item.field_name",
                "drug_attr_field_lov_item.value",
                "drug_attr_field_lov_item.importer_name",
            ],
            initially="DEFERRED",
        ),
        ForeignKeyConstraint(
            name="composite_foreign_key_drug_attr_multi_ref_val__field_def",
            columns=["field_name", "importer_name"],
            refcolumns=[
                "drug_attr_field_definition.field_name",
                "drug_attr_field_definition.importer_name",
            ],
            initially="DEFERRED",
        ),
        {"comment": "Definition of dataset specific fields and lookup fields"},
    )

    drug_id: uuid.UUID = Field(
        foreign_key="drug.id",
        primary_key=True,
        ondelete="CASCADE",
    )
    field_name: str = Field(primary_key=True)
    value_index: int = Field(primary_key=True)
    value: Optional[str] = Field(
        default=None,
        description="Generic storage of multiple reference value as list of string. Can be typed via the function in DrugAttrFieldDefinition.type",
    )
    importer_name: str = Field()
    """
    field_definition: DrugAttrFieldDefinition = Relationship()
    
    field_definition: DrugAttrFieldDefinition = Relationship(
        sa_relationship=RelationshipProperty(
            "DrugAttrFieldDefinition",
            foreign_keys="[DrugValMultiRef.importer_name,DrugValMultiRef.field_name]",
            primaryjoin="and_(DrugValMultiRef.importer_name==DrugAttrFieldDefinition.importer_name, DrugValMultiRef.field_name==DrugAttrFieldDefinition.field_name)",
            # back_populates="list_of_values",
        ),
    )
    """
    lov_item: DrugAttrFieldLovItem = Relationship(
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    drug: "DrugData" = Relationship(back_populates="attrs_multi_ref")


from pydantic import BaseModel


class DrugAttrRefApiRead(BaseModel):
    value: str | int | float | bool
    display: str
    ref_list_path: str
