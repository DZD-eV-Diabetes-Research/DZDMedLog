# Darreichungsform-Schlüsselverzeichnis
import uuid
from typing import List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# from medlogserver.db.wido_gkv_arzneimittelindex.model.stamm import Stamm

# TB: Model fertig. ungetestet


class Darreichungsform(DrugModelTableBase, table=True):
    __tablename__ = "drug_darrform"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "darrform.txt"

    darrform: str = Field(
        description="Darreichungsform",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
    # stamms: List["Stamm"] = Relationship(back_populates="darrform_ref")
