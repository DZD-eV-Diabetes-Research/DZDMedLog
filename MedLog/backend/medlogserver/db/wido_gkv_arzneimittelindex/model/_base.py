from sqlmodel import Field, String
from medlogserver.db.base import Base, BaseTable


class DrugModelTableBase(Base, BaseTable):
    dateiversion: str = Field(
        description="Dateiversion",
        sa_type=String(3),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:0"},
        primary_key=True,
        foreign_key="ai_dataversion.dateiversion",
    )
    datenstand: str = Field(
        description="Monat Datenstand (JJJJMM)",
        sa_type=String(6),
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:1"},
        primary_key=True,
        foreign_key="ai_dataversion.datenstand",
    )
