from typing import List, Dict, Type, Optional
import uuid
import datetime
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
from pydantic import create_model
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.user import User


class DrugCustomCreate(DrugModelTableBase, table=False):
    trade_name: str = Field(index=True)
    market_access_date: Optional[datetime.date] = Field(default=None)
    market_exit_date: Optional[datetime.date] = Field(default=None)
    custom_drug_notes: Optional[str] = Field(
        description="Additional notes for the custom drug."
    )
    attrs: List[DrugAttr]
    ref_attrs: List[DrugRefAttr]
    codes: List[DrugCode]


class Drug(DrugModelTableBase, table=True):
    __tablename__ = "drug"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    source_dataset_id: uuid.UUID = Field(foreign_key="drug_dataset_version.id")
    trade_name: str = Field(index=True)
    market_access_date: Optional[datetime.date] = Field(default=None)
    market_exit_date: Optional[datetime.date] = Field(default=None)
    is_custom_drug: bool = Field(
        default=False,
        description="User can create placeholder drugs, if the drug they try to document is not listed yet.",
    )
    custom_drug_notes: Optional[str] = Field(
        description="If custom drug is defined the user can enter some notes here."
    )
    custom_created_by: Optional[uuid.UUID] = Field(
        default=None,
        description="If Drug is created by user as a custom drug the user id will be saved here.",
        foreign_key="user.id",
    )
    attrs: List[DrugAttr] = Relationship(
        back_populates="drug",
        sa_relationship_kwargs={"lazy": "selectin"},
        cascade_delete=True,
    )
    ref_attrs: List[DrugRefAttr] = Relationship(
        back_populates="drug",
        sa_relationship_kwargs={"lazy": "selectin"},
        cascade_delete=True,
    )
    codes: List[DrugCode] = Relationship(
        back_populates="drug",
        sa_relationship_kwargs={"lazy": "selectin"},
        cascade_delete=True,
    )
    source_dataset: DrugDataSetVersion = Relationship()
