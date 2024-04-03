from typing import List, Self
from sqlmodel import Field, String, UUID
from pydantic import field_validator, model_validator

from medlogserver.model._base_model import MedLogBaseModel, BaseTable
import uuid


class DrugModelTableEnumBase(MedLogBaseModel, BaseTable):

    @classmethod
    def is_enum_table(self) -> bool:
        return True

    @classmethod
    def get_static_data(self) -> List[Self]:
        raise NotImplementedError()


class DrugModelTableBase(MedLogBaseModel, BaseTable):

    @classmethod
    def is_enum_table(self) -> bool:
        return False

    @classmethod
    def get_source_csv_filename(self) -> str:
        raise NotImplementedError()

    ai_version_id: uuid.UUID = Field(
        description="Foreing key to 'AiDataVersion' ('GKV WiDo Arzneimittel Index' Data Format Version) which contains the information which Arzneimittel Index 'Datenstand' and 'Dateiversion' the row has",
        foreign_key="ai_dataversion.id",
        primary_key=True,
    )
