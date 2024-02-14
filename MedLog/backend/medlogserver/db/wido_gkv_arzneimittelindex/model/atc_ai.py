# ATC-Klassifikation des GKV-Arzneimittelindex mit ATC-Code, ATC - Bedeutung

import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column


from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase


# TB: Model fertig. ungetestet


class ATCKlassifikation(DrugModelTableBase, table=True):
    __tablename__ = "drug_atc_ai"
    gkvai_source_csv_filename: str = "atc-ai.txt"

    atccode: str = Field(
        description="ATC-Code (Klassifikation nach WIdO)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
