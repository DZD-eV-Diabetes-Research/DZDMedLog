# Normpackungsgrößen-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class Normpackungsgroessen(DrugModelTableBase, table=True):
    __tablename__ = "drug_normpackungsgroessen"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "normpackungsgroessen.txt"

    zuzahlstufe: str = Field(
        description="Normpackungsgröße. TB: I dont know where the term 'zuzahlstufe' is coming from. It does not make too much sense for me. Maybe historic artefact/bug in the Arzneimittelindex.",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
