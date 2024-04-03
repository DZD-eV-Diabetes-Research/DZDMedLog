# Recycelte Artikelnummern
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase

# TB: Model fertig. ungetestet (und siehe den Kommentar in zeile 33)


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
