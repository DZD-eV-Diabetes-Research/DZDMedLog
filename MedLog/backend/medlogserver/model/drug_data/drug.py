from typing import List, Self
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
from pydantic import create_model
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_extra import DrugExtraField
from medlogserver.model.drug_data.drug_code import DrugCode


class Drug(DrugModelTableBase):
    __tablename__ = "drug"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    source_dataset_id = Field(foreign_key="drug_dataset_version.id")
    trade_name: str = Field(index=True)
    # dosage_form_id: str = Field(description="darreichungsform")
    # administration_route: str = Field(description="applikationsform")
    extra_fields: List[DrugExtraField] = Relationship(back_populates="drug")
    codes: List[DrugCode] = Relationship(back_populates="drug")


"""
# https://www.getorchestra.io/guides/pydantic-dynamic-model-creation-in-fastapi
def 

DrugApiRead = create_model("DrugRead",)
"""
