# Sondercodes
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model Fertig, ungetestet


class Sondercodes(DrugModelTableBase, table=True):
    __tablename__ = "drug_sonder"
    gkvai_source_csv_filename: str = "sonder.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    sondercode: int = Field(
        description="Sondercodes(siehe Schlüsselverzeichnis sonderbedeutung.txt)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
