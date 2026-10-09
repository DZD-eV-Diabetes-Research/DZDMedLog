from typing import Any, Dict
import enum
from sqlmodel import Field, Column, JSON, String

from medlogserver.model._base_model import MedLogBaseModel, TimestampModel


class ExportSchemaFormat(str, enum.Enum):
    """Which export file a schema describes."""

    # JSON Schema (https://json-schema.org/) of the JSON export
    JSON = "json"
    # Frictionless Table Schema (https://datapackage.org/standard/table-schema/) of the CSV export
    CSV = "csv"


class ExportSchema(MedLogBaseModel, TimestampModel, table=True):
    """A schema of the study export, built by the `EXPORT_SCHEMA_BUILD` worker task (issue #387).

    The fixed part of the export is defined by the MedLog code, the drug part by the
    drug importer and the imported drug dataset (reference list values). A schema is
    therefore only valid for one combination of MedLog version and drug dataset version.
    """

    __tablename__ = "export_schema"
    __table_args__ = {
        "comment": "Schemas of the study export, one per MedLog version, drug dataset version and format. Built by a worker job, can be deleted at any time (they are rebuilt on startup)."
    }
    medlog_version: str = Field(primary_key=True)
    drug_dataset_version: str = Field(primary_key=True)
    format: ExportSchemaFormat = Field(sa_column=Column(String, primary_key=True))
    content: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
