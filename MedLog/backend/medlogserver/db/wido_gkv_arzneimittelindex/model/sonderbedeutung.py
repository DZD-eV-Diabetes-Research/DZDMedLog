# Sondercode-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase


# TB: Model fertig. ungetestet


class SondercodesTypes(DrugModelTableBase, table=True):
    __tablename__ = "drug_sonderbedeutung"
    gkvai_source_csv_filename: str = "sonderbedeutung.txt"

    sonder_atc_gruppe: str = Field(
        description="Sonder-ATC Gruppe",
        sa_type=String(2),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    bezeichnung: int = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
