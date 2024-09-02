from typing import List, Self, Optional
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)


class DrugDataSetVersion(DrugModelTableBase, table=True):
    __tablename__ = "drug_dataset_version"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dataset_version: str = Field(
        description="Must be sortable to determine which dataset is the latest",
    )
    dataset_name: str = Field()

    dataset_link: Optional[str] = Field(
        description="If the dataset has soome kind of Website or source info page, paste it here"
    )
