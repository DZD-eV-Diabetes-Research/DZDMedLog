# Arzneimittel - PRISCUS2 - Datei
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class ArzneimittelPriscus2(DrugModelTableBase, table=True):
    __tablename__ = "drug_priscus2pzn"
    gkvai_source_csv_filename: str = "priscus2pzn.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
