# Hersteller - Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class Hersteller(DrugModelTableBase, table=True):
    __tablename__ = "drug_hersteller"
    gkvai_source_csv_filename: str = "hersteller.txt"

    herstellercode: str = Field(
        description="Hersteller",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )