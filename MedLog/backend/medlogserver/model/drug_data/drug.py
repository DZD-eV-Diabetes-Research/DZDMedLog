from typing import List, Dict, Type
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
from pydantic import create_model
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr_field import DrugAttrField
from medlogserver.model.drug_data.drug_code import DrugCode


class Drug(DrugModelTableBase, table=True):
    __tablename__ = "drug"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    source_dataset_id: uuid.UUID = Field(foreign_key="drug_dataset_version.id")
    trade_name: str = Field(index=True)
    # dosage_form_id: str = Field(description="darreichungsform")
    # administration_route: str = Field(description="applikationsform")
    attr_fields: List[DrugAttrField] = Relationship(back_populates="drug")
    codes: List[DrugCode] = Relationship(back_populates="drug")
