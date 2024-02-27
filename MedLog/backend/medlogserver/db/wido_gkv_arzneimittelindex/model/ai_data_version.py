import uuid
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, UniqueConstraint
from sqlalchemy import String, Integer, Column

from medlogserver.db.base import BaseModel, BaseTable


class AiDataVersion(BaseModel, BaseTable, table=True):
    """This is a metadata table and not part of the official Wido GTK Arzneimittelindex.
    We track the "datenstand" and "dateiversion" variants of the source data here.


    Args:
        DrugModelTableBase (_type_): _description_
        table (bool, optional): _description_. Defaults to True.
    """

    __tablename__ = "ai_dataversion"
    __table_args__ = (
        UniqueConstraint(
            "dateiversion", "datenstand", name="arzneimittelindex_version_constraint"
        ),
    )
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
        schema_extra={"examples": ["aca335063279463395e6908f03ae0abb"]},
    )
    # https://www.wido.de/fileadmin/Dateien/Dokumente/Publikationen_Produkte/Arzneimittel-Klassifikation/wido_arz_stammdatei_plus_info_2021.pdf
    dateiversion: str = Field(
        description="Dateiversion",
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:0"},
        sa_type=String(3),
        schema_extra={"examples": ["52"]},
    )
    datenstand: str = Field(
        description="Monat Datenstand (JJJJMM)",
        sa_column_kwargs={"comment": "gkvai_source_csv_col_index:1"},
        sa_type=String(6),
        schema_extra={"examples": ["202301"]},
    )
    import_completed_at: Optional[datetime] = Field(
        default=None,
        description="When starting an import a new AiDataVersion will be made. on completion with no errors this field will be set and the whole Arzneimittelindex is 'armed'/'can be used' ",
    )
    deactivated: bool = Field(
        default=False,
        description="If set to true this arzneimittel index version will be ignored (when not queried for explciet in the crud interface). This can be helpfull e.g. if the last import contained dirty data and one wants to fallback on the previous version.",
    )
