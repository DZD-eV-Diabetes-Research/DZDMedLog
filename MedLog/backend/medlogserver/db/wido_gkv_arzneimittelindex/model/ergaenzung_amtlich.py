# Abweichungen amtlicher ATC Code mit DDD
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class AbweichungenAmtlicherATC(DrugModelTableBase, table=True):
    __tablename__ = "drug_ergaenzung_amtlich"
    gkvai_source_csv_filename: str = "ergaenzung_amtlich.txt"
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
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:1"},
        primary_key=True,
    )
    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    atccode: str = Field(
        description="ATC-Code (amtliche Klassifikation)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )

    dddpk: str = Field(
        description="DDD je Packung (nach amtlicher Klassifikation, in 1/1000 Einheiten)",
        sa_type=String(9),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:4"},
    )
