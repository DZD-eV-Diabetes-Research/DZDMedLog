from typing import List, Self, Optional, Literal
import uuid
import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import (
    DrugModelTableBase,
)


class DrugDataSetVersion(DrugModelTableBase, table=True):
    __tablename__ = "drug_dataset_version"
    __table_args__ = {
        "comment": "Tracks different version of same drug indexes that were imported"
    }
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dataset_version: str = Field(
        description="Must be sortable to determine which dataset is the latest",
    )
    dataset_source_name: str = Field(
        description="If a drugdataset has multiple versions the 'dataset_name' is the key to group them."
    )

    dataset_link: Optional[str] = Field(
        description="If the dataset has some kind of Website or source info page, paste it here"
    )
    is_custom_drugs_collection: bool = Field(
        default=False,
        description="Every drug dataset source has a 'special' version that will group custom drugs",
    )
    current_active: Optional[bool] = Field(
        description="States if this dataset used in the backend or just archived. Only one dataset is allowed to be active."
    )
    import_file_path: Optional[str] = Field(
        default=None, description="The source file for the drug data import."
    )
    import_status: Literal["queued", "running", "failed" "done"] = Field(
        default="queued",
        description="Is the data for this drug data set allready imported.",
        sa_column=Column(
            String
        ),  # , sa_column=Column(String) -> https://github.com/fastapi/sqlmodel/issues/57 + https://github.com/fastapi/sqlmodel/issues/67
    )
    import_error: Optional[str] = Field(
        default=None,
        description="If the drug data import failes, the error stacktrace will be logged here.",
    )
    import_start_datetime_utc: datetime.datetime = Field(
        description="Datetime when the imported for this drug dataset was started"
    )

    import_end_datetime_utc: Optional[datetime.datetime] = Field(
        default=None,
        description="Datetime when the imported for this drug dataset was started",
    )
