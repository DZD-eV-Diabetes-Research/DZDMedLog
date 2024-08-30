from typing import List, Self
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug import Drug

class DrugCode(DrugModelTableBase, table=True):
    __tablename__ = "drug_dataset_version"
    __table_args__ = {"comment": "Tracks different version of same drug indexes that were imported"}
    id:uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True)
    drug_id: uuid.UUID = Field(primary_key=True,foreign_key="drug.id")
    code_system: str = Field(primary_key=True,foreign_key="drug_national_code_system.id")
    code:str
