# Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung
import uuid
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column

from medlogserver.model.wido_gkv_arzneimittelindex._base import DrugModelTableBase

# TB: Model fertig. ungetestet


class ATCAmtlich(DrugModelTableBase, table=True):
    __tablename__ = "drug_atc_amtlich"
    __table_args__ = {
        "comment": "Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung"
    }

    @classmethod
    def get_source_csv_filename(self) -> str:
        return "atc-amtlich.txt"

    atccode: str = Field(
        description="ATC-Code (amtliche Klassifikation)",
        sa_type=String(7),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:2"},
        primary_key=True,
    )

    bedeutung: str = Field(
        description="Bedeutung",
        sa_type=String(200),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
    )
