# Sondercodes
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.base import Base, BaseTable

# TB: Model Fertig, ungetestet


class Sondercodes(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "sonder.txt"
    dateiversion: str = Field(
        description="Dateiversion",
        sa_type=String(3),
        schema_extra={
            "gkvai_source_csv_col_index": 0,
        },
        primary_key=True,
    )
    datenstand: str = Field(
        description="Monat Datenstand (JJJJMM)",
        sa_type=String(6),
        schema_extra={"gkvai_source_csv_col_index": 1},
        primary_key=True,
    )
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 2},
        primary_key=True,
    )
    sondercode: int = Field(
        description="Sondercodes(siehe Schlüsselverzeichnis sonderbedeutung.txt)",
        sa_type=SmallInteger,
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
