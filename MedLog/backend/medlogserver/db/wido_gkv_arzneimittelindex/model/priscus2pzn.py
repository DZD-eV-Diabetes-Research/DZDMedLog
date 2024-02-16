# Arzneimittel - PRISCUS2 - Datei
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class Priscus2PZN(DrugModelTableBase, table=True):
    __tablename__ = "drug_priscus2pzn"

    __table_args__ = {
        "comment": "Arzneimittel-PRISCUS2-Datei. From info_stammdatei_plus.pdf: In der PRISCUS-2.0-PZN-Liste werden Arzneimittel gelistet, die für ältere Menschen als potenziell inadäquate Medikation (PIM) bewertet werden."
    }

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "priscus2pzn.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
