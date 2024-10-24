# Recycelte Artikelnummern
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


class RecycledPZN(DrugModelTableBase, table=True):
    __tablename__ = "drug_recycle"
    __table_args__ = {
        "comment": "Recycelte Artikelnummern. From info_stammdatei_plus.pdf: eine Liste von Pharmazentralnummern enthält, die früher bereits genutzt worden sind, nun aber einem neuen Artikel zugewiesen wurden"
    }

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "recycle.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    neu_rein: str = Field(
        description="Enddatum (JJJJMM)",
        sa_type=String(6),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
