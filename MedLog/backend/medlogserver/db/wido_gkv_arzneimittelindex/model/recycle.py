# Recycelte Artikelnummern
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet (und siehe den Kommentar in zeile 33)


class RecycelteArtikelnummern(DrugModelTableBase, table=True):
    __tablename__ = "drug_recycle"
    gkvai_source_csv_filename: str = "recycle.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    neu_rein: str = Field(
        description="Enddatum",  # hier war kein Datumsformat in der Tabelle angegeben
        sa_type=String(6),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
