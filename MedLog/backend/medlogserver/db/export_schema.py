from typing import List, Optional
from sqlmodel import select, delete, or_

from medlogserver.db._base_crud import DatabaseInteractionBase
from medlogserver.model.export_schema import ExportSchema, ExportSchemaFormat
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class ExportSchemaCRUD(DatabaseInteractionBase):
    async def get(
        self,
        medlog_version: str,
        drug_dataset_version: str,
        format_: ExportSchemaFormat,
        raise_exception_if_none: Optional[Exception] = None,
    ) -> Optional[ExportSchema]:
        query = select(ExportSchema).where(
            ExportSchema.medlog_version == medlog_version,
            ExportSchema.drug_dataset_version == drug_dataset_version,
            ExportSchema.format == ExportSchemaFormat(format_).value,
        )
        result = await self.session.exec(statement=query)
        export_schema = result.one_or_none()
        if export_schema is None and raise_exception_if_none:
            raise raise_exception_if_none
        return export_schema

    async def list_formats(
        self, medlog_version: str, drug_dataset_version: str
    ) -> List[ExportSchemaFormat]:
        """The formats a schema exists for, for this version combination."""
        query = select(ExportSchema.format).where(
            ExportSchema.medlog_version == medlog_version,
            ExportSchema.drug_dataset_version == drug_dataset_version,
        )
        result = await self.session.exec(statement=query)
        return [ExportSchemaFormat(format_) for format_ in result.all()]

    async def replace_all(self, export_schemas: List[ExportSchema]):
        """Store `export_schemas` and delete the schemas of all other version combinations.

        A schema is only valid for one MedLog version and drug dataset version, so the
        rows of earlier versions are obsolete. Without the cleanup every dev build
        (the version changes with every commit) would leave its rows behind.
        """
        for export_schema in export_schemas:
            await self.session.merge(export_schema)
        keys = {(s.medlog_version, s.drug_dataset_version) for s in export_schemas}
        if keys:
            await self.session.exec(
                delete(ExportSchema).where(
                    *[
                        or_(
                            ExportSchema.medlog_version != medlog_version,
                            ExportSchema.drug_dataset_version != drug_dataset_version,
                        )
                        for medlog_version, drug_dataset_version in keys
                    ]
                )
            )
        await self.session.commit()
