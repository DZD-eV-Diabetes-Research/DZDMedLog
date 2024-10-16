# Abweichungen amtlicher ATC Code mit DDD
import uuid
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


class ATCErgaenzungAmtlich(DrugModelTableBase, table=True):
    __tablename__ = "drug_ergaenzung_amtlich"
    __table_args__ = {
        "comment": "Abweichungen amtlicher ATC Code mit DDD (Für details siehe info_stammdatei_plus.pdf Punkt 10) )"
    }

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "ergaenzung_amtlich.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    atccode: Optional[str] = Field(
        description="ATC-Code (amtliche Klassifikation)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )

    dddpk: Optional[str] = Field(
        description="DDD (defined daily dose / Tagestherapiedosis) je Packung (nach amtlicher Klassifikation, in 1/1000 Einheiten)",
        sa_type=String(9),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:4"},
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
