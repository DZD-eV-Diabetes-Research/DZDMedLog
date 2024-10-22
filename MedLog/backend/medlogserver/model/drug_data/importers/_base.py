from typing import Dict, List, AsyncIterator
from pathlib import Path
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug import Drug


class DrugDataSetImporterBase:
    def __init__(self):
        self.dataset_name = "Base Example"
        self.dataset_link = "Base Example"
        self.api_name = "baseexample"
        self.source_dir: Path = None
        self.version: str = None

    async def generate_drug_data_set_definition(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version=self.version,
            dataset_source_name=self.dataset_name,
            dataset_link=self.dataset_link,
        )

    async def generate_custom_drug_set_definition(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version="Custom",
            is_custom_drugs_collection=True,
            dataset_source_name=self.dataset_name,
        )

    async def get_ref_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        raise NotImplementedError()

    async def get_code_definitions(self) -> List[DrugCodeSystem]:
        raise NotImplementedError()

    async def get_drug_items(self) -> AsyncIterator[Drug]:
        raise NotImplementedError()

    async def run_import(self, source_dir: Path, version: str):
        raise NotImplementedError()
