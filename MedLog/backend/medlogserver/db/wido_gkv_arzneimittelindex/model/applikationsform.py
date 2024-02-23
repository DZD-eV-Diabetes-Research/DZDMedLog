# Applikationsform-Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.db.wido_gkv_arzneimittelindex.model._base import DrugModelTableBase


class Applikationsform(DrugModelTableBase, table=True):
    __tablename__ = "drug_applikationsform"
    __table_args__ = {"comment": "Applikationsform-Schlüsselverzeichnis"}

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "applikationsform.txt"

    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf

    appform: str = Field(
        description="Applikationsform",
        sa_type=String(5),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
        schema_extra={"examples": ["IMP"]},
    )
    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        schema_extra={"examples": ["Implantat"]},
    )
