from typing import List, Self, Optional, Literal
import uuid
import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import String, Integer, Column, SmallInteger

from medlogserver.model.drug_data._base import DrugModelTableBase, TimestampModel


class DrugDataSetVersion(DrugModelTableBase, TimestampModel, table=True):
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
    import_status: Literal["queued", "running", "failed" "done"] = Field(
        default="queued",
        description="Is the data for this drug data set allready imported.",
        sa_column=Column(
            String
        ),  # , sa_column=Column(String) -> https://github.com/fastapi/sqlmodel/issues/57 + https://github.com/fastapi/sqlmodel/issues/67
    )
    import_file_path: str = Field(default=None)
    import_start_datetime_utc: Optional[datetime.datetime] = Field(
        default=None,
        description="Datetime when the imported for this drug dataset was started",
    )
    import_end_datetime_utc: Optional[datetime.datetime] = Field(
        default=None,
        description="Datetime when the imported for this drug dataset was started",
    )
