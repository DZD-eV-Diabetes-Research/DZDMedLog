# Änderungsdienst
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

import enum


class JaNein(str, enum.Enum):
    Ja = 1
    Nein = 2


class StammAenderungen(DrugModelTableBase, table=True):
    __tablename__ = "drug_aenderungen"
    gkvai_source_csv_filename: JaNein = "stamm_aenderungen.txt"
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
    laufnr: JaNein = Field(
        description="Laufende Nummer (vom WIdO vergeben)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
    stakenn: JaNein = Field(
        description="(Sämtliche Arzneimittel eines Handelsnamens)Standardaggregatkennung (zu Lfd. Nr.)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:4"},
    )
    staname: JaNein = Field(
        description="Standardaggregatname (vom WIdO vergeben)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:5"},
    )
    atc_code: JaNein = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:6"},
    )
    indgr: JaNein = Field(
        description="Indikationsgruppe (nach Roter Liste 2014)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:7"},
    )
    dddpk: JaNein = Field(
        description="Geänderte DDD je Packung (nach WIdO, in 1/1000 Einheiten)",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:8"},
    )
    apopflicht: JaNein = Field(
        description="Geänderte Apotheken-/Rezeptpflicht",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:9"},
    )
    generikakenn: JaNein = Field(
        description="Geänderte Generika-Kennung",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:10"},
    )
    appform: JaNein = Field(
        description="Geänderte Applikationsform",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:11"},
    )
    biosimilar: JaNein = Field(
        description="Geänderter Biosimilar Status",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
    )
    orphan: JaNein = Field(
        description="Geänderter Orphan Drug Status",
        sa_type=SmallInteger,
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:13"},
    )
