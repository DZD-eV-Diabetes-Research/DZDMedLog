# Sondercode-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


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
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
