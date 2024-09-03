from typing import List, Callable, Tuple, Dict, Optional
from pathlib import Path
import csv
from dataclasses import dataclass

from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr_field import DrugAttrField
from medlogserver.model.drug_data.drug_attr_field_definitions import (
    DrugAttrFieldDefinition,
    ValueTypeCasting,
)
from medlogserver.model.drug_data.drug_attr_field_definitions_lov import (
    DrugAttrFieldDefinitionLovItem,
)

from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase


@dataclass
class DrugAttrFieldLovDefinition:
    lov_source_file: str
    lov_source_headers: List[str]
    values_col_name: str
    display_value_col_name: str


@dataclass
class DrugAttrLovFieldDefinitionContainer:
    field: DrugAttrFieldDefinition
    lov: Optional[DrugAttrFieldLovDefinition] = None


class WidoAiImporter(DrugDataSetImporterBase):
    def __init__(self, source_dir: Path, version: str):
        self.dataset_name = "Wido GKV Arzneimittelindex"
        self.dataset_link = (
            "https://www.wido.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        )
        self.source_dir = source_dir
        self.version = version

    async def get_attr_field_definitions(self) -> List[DrugAttrFieldDefinition]:
        field_def_containers = await self._get_attr_definitons_with_lov_dev()
        return [field_cont.field for name, field_cont in field_def_containers.items()]

    async def run(self):
        field_objs = await self._get_attr_definitons()

        lov_field_objects = await self._get_attr_definitons_with_lov_dev()
        for field_name, lov_field_obj in lov_field_objects.items():
            field_objs.append(lov_field_obj.field)
            field_objs.extend(
                await self._generate_lov_items(
                    lov_field_obj.field, lov_definition=lov_field_obj.lov
                )
            )
        await self.commit(field_objs)

    async def commit(self, objs):
        async with get_async_session_context() as session:
            session.add_all(objs)
            await session.commit()

    async def _get_attr_definitons(self) -> List[DrugAttrFieldDefinition]:
        """
            packgroesse: Optional[int] = Field(
            default=None,
            description="Packungsgröße (in 1/10 Einheiten)",
            sa_type=Integer,
            sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
            schema_extra={"examples": ["1000"]},
        )
        """
        fields = []
        fields.append(
            DrugAttrFieldDefinition(
                field_name="packgroesse",
                field_desc="Packungsgröße (in 1/10 Einheiten)",
                type=ValueTypeCasting.INT,
                has_list_of_values=False,
            )
        )
        return fields

    async def _get_attr_definitons_with_lov_dev(
        self,
    ) -> Dict[str, DrugAttrLovFieldDefinitionContainer]:
        fields = {}
        fields["darreichungsform"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="darreichungsform",
                field_desc="Darreichungsform (eng: dosage form)",
                type=None,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovDefinition(
                lov_source_file="darrform.txt",
                lov_source_headers=[
                    "Dateiversion",
                    "Datenstand",
                    "darrform",
                    "bedeutung",
                ],
                values_col_name="darrform",
                display_value_col_name="bedeutung",
            ),
        )
        fields["applikationsform"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="applikationsform",
                field_desc="applikationsform (eng: administration route)",
                type=None,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovDefinition(
                lov_source_file="applikationsform.txt",
                lov_source_headers=[
                    "Dateiversion",
                    "Datenstand",
                    "appform",
                    "bedeutung",
                ],
                values_col_name="appform",
                display_value_col_name="bedeutung",
            ),
        )
        fields["hersteller"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="hersteller",
                field_desc="hersteller (eng: producer)",
                type=None,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovDefinition(
                lov_source_file="hersteller.txt",
                lov_source_headers=[
                    "Dateiversion",
                    "Datenstand",
                    "herstellercode",
                    "bedeutung",
                ],
                values_col_name="herstellercode",
                display_value_col_name="bedeutung",
            ),
        )
        return fields

    async def _generate_lov_items(
        self, paren_field: DrugAttrField, lov_definition: DrugAttrFieldLovDefinition
    ) -> List[DrugAttrFieldDefinitionLovItem]:
        # darrform_txt_headers = ["Dateiversion", "Datenstand", "darrform", "bedeutung"]
        lov_items: List[DrugAttrFieldDefinitionLovItem] = []
        with open(Path(self.source_dir, lov_definition.lov_source_file)) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for index, row in enumerate(csvreader):
                value = row[
                    lov_definition.lov_source_headers.index(
                        lov_definition.values_col_name
                    )
                ]
                display_value = row[
                    lov_definition.lov_source_headers.index(
                        lov_definition.display_value_col_name
                    )
                ]
                li = DrugAttrFieldDefinitionLovItem(
                    field=paren_field,
                    value=value,
                    display_value=display_value,
                    sort_order=index,
                )
                lov_items.append(li)
        return lov_items
