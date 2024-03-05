# Sondercode-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


# TB: Model fertig. ungetestet


class SondercodeBedeutung(DrugModelTableBase, table=True):
    __tablename__ = "drug_sonderbedeutung"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "sonderbedeutung.txt"

    sonder_atc_gruppe: str = Field(
        description="Sonder-ATC Gruppe. Anmerkung. Unglückliche Bezeichung seitens GKV. Verständlicher wäre 'sondercode' oder 'sondercode_atc_gruppe' um auf die relation zu sonder.sondercode hinzuweisen.",
        sa_type=String(2),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    bezeichnung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
