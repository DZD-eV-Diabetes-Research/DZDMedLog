# Normpackungsgrößen-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable

# TB: Model fertig. ungetestet


class Normpackungsgroessen(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "normpackungsgroessen.txt"
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

    zuzahlstufe: str = Field(
        description="Normpackungsgröße",
        sa_type=String(1),
        schema_extra={"gkvai_source_csv_col_index": 2},
        primary_key=True,
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
