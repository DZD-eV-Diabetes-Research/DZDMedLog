from typing import List, Self, TYPE_CHECKING
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem

if TYPE_CHECKING:
    from medlogserver.model.drug_data.drug import Drug


class DrugCodeApiRead(SQLModel):
    code_system: str = Field()
    code: str = Field()


class DrugCode(DrugModelTableBase, DrugCodeApiRead, table=True):
    __tablename__ = "drug_code"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    drug_id: uuid.UUID = Field(primary_key=True, foreign_key="drug.id")
    code_system_id: str = Field(primary_key=True, foreign_key="drug_code_system.id")
    code: str = Field()
    drug: "Drug" = Relationship(back_populates="codes")
    code_system: DrugCodeSystem = Relationship()
