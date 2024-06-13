# Normpackungsgrößen-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


class Normpackungsgroessen(DrugModelTableBase, table=True):
    __tablename__ = "drug_normpackungsgroessen"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "normpackungsgroessen.txt"

    zuzahlstufe: str = Field(
        description="""Normpackungsgröße. Tim: I dont know where the term 'zuzahlstufe' is coming from. 
        It does not make too much sense for me and its confusing compared to the table name `Normpackungsgroessen`. 
        Maybe historic artefact/bug in the Arzneimittelindex or i am just stupid.
        If this assumption is correct, a better designation for this column would be sth. like `normpackungsgroessen_id` or `normpackungsgroessen_code`""",
        sa_type=String(1),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
        schema_extra={"examples": ["E"]},
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        schema_extra={"examples": ["N1+N3"]},
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
