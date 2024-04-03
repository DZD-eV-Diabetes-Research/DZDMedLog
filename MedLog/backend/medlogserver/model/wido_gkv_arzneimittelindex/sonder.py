# Sondercodes
import uuid
from sqlmodel import Field, SQLModel, String
from sqlalchemy import String, Integer, Column, SmallInteger
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase

# TB: Model Fertig, ungetestet


class Sondercodes(DrugModelTableBase, table=True):
    __tablename__ = "drug_sonder"
    # On composite foreign keys https://github.com/tiangolo/sqlmodel/issues/222
    __table_args__ = (
        ForeignKeyConstraint(
            name="composite_foreign_key_sondercode_bedeutung",
            columns=["ai_dataversion_id", "sondercode"],
            refcolumns=[
                "drug_sonderbedeutung.ai_dataversion_id",
                "drug_sonderbedeutung.sonder_atc_gruppe",
            ],
        ),
        {"comment": ""},
    )

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "sonder.txt"

    pzn: str = Field(
        description="Pharmazentralnummer",
        sa_type=String(8),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )
    sondercode: str = Field(
        description="Sondercodes(siehe Schlüsselverzeichnis sonderbedeutung.txt)",
        sa_type=String(2),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
        # foreign_key="drug_sonderbedeutung.sonder_atc_gruppe",
    )
    ai_dataversion_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        # foreign_key="ai_dataversion.id",
        default=None,
        primary_key=True,
        sa_column_args=[ForeignKey("ai_dataversion.id", ondelete="CASCADE")],
    )
