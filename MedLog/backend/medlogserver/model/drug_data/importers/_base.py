from typing import Dict, List
from pathlib import Path
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem


class DrugDataSetImporterBase:
    def __init__(self, source_dir: Path, version: str):
        self.dataset_name = "Base Example"
        self.dataset_link = "Base Example"
        self.api_name = "baseexample"
        self.source_dir = source_dir
        self.version = version

    async def get_drug_data_set(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version=self.version,
            dataset_name=self.dataset_name,
            dataset_link=self.dataset_link,
        )

    async def get_ref_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_code_definitions(self) -> List[DrugCodeSystem]:
        raise NotImplementedError()
