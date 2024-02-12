# Recycelte Artikelnummern
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable

# TB: Model fertig. ungetestet (und siehe den Kommentar in zeile 33)


class RecycelteArtikelnummern(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "recycle.txt"
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

    neu_rein: str = Field(
        description="Enddatum",  # hier war kein Datumsformat in der Tabelle angegeben
        sa_type=String(6),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
