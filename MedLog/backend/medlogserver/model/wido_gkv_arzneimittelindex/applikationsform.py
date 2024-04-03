# Applikationsform-Schlüsselverzeichnis
from typing import Optional
import uuid
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey, UUID
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase
from medlogserver.model.wido_gkv_arzneimittelindex.ai_data_version import AiDataVersion


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
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
