from sqlmodel import Field, String, UUID
from pydantic import field_validator, model_validator

from medlogserver.db.base import Base, BaseTable
import uuid


class DrugModelTableBase(Base, BaseTable):
    @classmethod
    def get_source_csv_filename(self) -> str:
        raise NotImplementedError()

    ai_version_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' which contains the information which 'Datenstand' and 'Dateiversion' the row has",
        foreign_key="ai_dataversion.id",
        primary_key=True,
    )
