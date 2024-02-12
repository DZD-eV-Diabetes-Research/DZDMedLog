# Hersteller - Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable

# TB: Model fertig. ungetestet

class Hersteller(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "hersteller.txt"
    dateiversion: str = Field(
        description="Dateiversion",
        sa_type=String(3),
        schema_extra={
            "gkvai_source_csv_col_index": 0,
        },
    )

    datenstand: str = Field(
        description="Monat Datenstand (JJJJMM)",
        sa_type=String(6),
        schema_extra={"gkvai_source_csv_col_index": 1},
    )

    herstellercode: str = Field(
        description="Hersteller",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 2},
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
