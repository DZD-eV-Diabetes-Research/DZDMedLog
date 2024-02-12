# Sondercode-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.base import Base, BaseTable


# TB: Model fertig. ungetestet


class SondercodesTypes(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "sonderbedeutung.txt"
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
    sonder_atc_gruppe: str = Field(
        description="Sonder-ATC Gruppe",
        sa_type=String(2),
        schema_extra={"gkvai_source_csv_col_index": 2},
        primary_key=True,
    )
    bezeichnung: int = Field(
        description="Bedeutung",
        sa_type=String(200),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
