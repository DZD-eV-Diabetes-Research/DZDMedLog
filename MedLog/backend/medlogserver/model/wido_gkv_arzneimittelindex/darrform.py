# Darreichungsform-Schlüsselverzeichnis
import uuid
from typing import List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase

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
        schema_extra={"examples": ["ZKA"]},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        schema_extra={"examples": ["Zerbeißkapsel"]},
    )
    # stamms: List["Stamm"] = Relationship(back_populates="darrform_ref")
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
