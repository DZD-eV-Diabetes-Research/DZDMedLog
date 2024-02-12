# Abweichungen amtlicher ATC Code mit DDD
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable

# TB: Model fertig. ungetestet


class AbweichungenAmtlicherATC(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "ergaenzung_amtlich.txt"
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
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        schema_extra={"gkvai_source_csv_col_index": 2},
    )
    atccode: str = Field(
        description="ATC-Code (amtliche Klassifikation)",
        sa_type=String(7),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )

    dddpk: str = Field(
        description="DDD je Packung (nach amtlicher Klassifikation, in 1/1000 Einheiten)",
        sa_type=String(9),
        schema_extra={"gkvai_source_csv_col_index": 4},
    )
