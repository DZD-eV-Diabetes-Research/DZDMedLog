# Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


class ATCAmtlich(DrugModelTableBase, table=True):
    __tablename__ = "drug_atc_amtlich"
    __table_args__ = {
        "comment": "Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung"
    }

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "atc-amtlich.txt"

    atccode: str = Field(
        description="ATC-Code (amtliche Klassifikation)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    bedeutung: str = Field(
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
