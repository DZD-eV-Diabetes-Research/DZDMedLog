from typing import List, Dict, Type
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column, SmallInteger
from pydantic import create_model
from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug_code import DrugCode


class DrugSearchCache(DrugModelTableBase, table=True):
    __tablename__ = "drug"
    __table_args__ = {
        "comment": "Aggregates and indexes drug attributtes for the current drug dataset, for faster search."
    }
    id: uuid.UUID = Field(
        primary_key=True,
        foreign_key="drug.id",
        description="one to one relation to a drug",
    )
    search_cache_field: str = Field(
        index=True,
        description="All searchable fields and ref_fields (values and display) aggregated into one indexed string",
    )
    search_cache_codes: str = Field(
        index=True,
        description="All drug codes aggregated into one indexed string",
    )
