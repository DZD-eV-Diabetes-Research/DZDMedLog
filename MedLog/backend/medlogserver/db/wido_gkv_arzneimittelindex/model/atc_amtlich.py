# Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class AmtlicheATCKlassifikation(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "atc-amtlich.txt"
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
    atc_code: str = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=String(7),
        schema_extra={"gkvai_source_csv_col_index": 2},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
