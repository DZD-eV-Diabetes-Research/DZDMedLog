# Applikationsform-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import Base, BaseTable


class Applikationsform(Base, BaseTable, table=True):
    gkvai_source_csv_filename: str = "applikationsform.txt"
    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
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
    appform: str = Field(
        description="Applikationsform",
        sa_type=String(5),
        schema_extra={"gkvai_source_csv_col_index": 2},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        schema_extra={"gkvai_source_csv_col_index": 3},
    )
