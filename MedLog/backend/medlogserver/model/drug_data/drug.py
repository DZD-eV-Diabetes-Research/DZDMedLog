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


class Drug(DrugModelTableBase, table=True):
    __tablename__ = "drug"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    source_dataset_id: uuid.UUID = Field(foreign_key="drug_dataset_version.id")
    trade_name: str = Field(index=True)
    market_launch_at: Optional[datetime.date] = Field(default=None)
    market_withdrawal_at: Optional[datetime.date] = Field(default=None)
    attrs: List[DrugAttr] = Relationship(
        back_populates="drug", sa_relationship_kwargs={"lazy": "selectin"}
    )
    ref_attrs: List[DrugRefAttr] = Relationship(
        back_populates="drug", sa_relationship_kwargs={"lazy": "selectin"}
    )
    codes: List[DrugCode] = Relationship(
        back_populates="drug", sa_relationship_kwargs={"lazy": "selectin"}
    )
    source_dataset: DrugDataSetVersion = Relationship()
