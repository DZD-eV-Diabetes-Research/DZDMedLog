# Hersteller - Schlüsselverzeichnis
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column
from sqlalchemy import ForeignKey
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase


class Hersteller(DrugModelTableBase, table=True):
    __tablename__ = "drug_hersteller"

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "hersteller.txt"

    herstellercode: str = Field(
        description="Hersteller",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
        schema_extra={"examples": ["BEHR"]},
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(70),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        schema_extra={"examples": ["Behring Applied Technology"]},
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
