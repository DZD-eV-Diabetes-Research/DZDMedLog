from typing import List, Callable, Tuple
from pathlib import Path
import csv

from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_extra_field import DrugExtraField
from medlogserver.model.drug_data.drug_extra_field_definitions import (
    DrugExtraFieldDefinition,
    ValueCastingFunc,
)
from medlogserver.model.drug_data.drug_extra_field_definitions_lov import (
    DrugExtraFieldDefinitionLovItem,
)
from dataclasses import dataclass


@dataclass
class LovGenContainer:
    lov_source_file: str
    lov_source_headers: List[str]
    values_col_name: str
    display_value_col_name: str


class WidoAiImporter:
    def __init__(self, source_dir: Path, version: str):
        self.dataset_name = "Wido GKV Arzneimittelindex"
        self.dataset_link = (
            "https://www.wido.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        )
        self.source_dir = source_dir
        self.version = version

    async def run(self):
        field_objs = await self.get_extra_lov_fields()
        await self.commit(field_objs)

    async def commit(self, objs):
        async with get_async_session_context() as session:
            session.add_all(objs)
            await session.commit()

    async def get_extra_lov_fields(self):
        db_obj = []
        # darrform
        darrform_field, darrform_field_lov_items = await self.generate_field(
            name="darreichungsform",
            desc="Darreichungsform (eng: dosage form)",
            type_cast=None,
            lov_params=LovGenContainer(
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
        db_obj.append(darrform_field)
        db_obj.extend(darrform_field_lov_items)
        ## Applikationsform
        darrform_field, darrform_field_lov_items = await self.generate_field(
            name="applikationsform",
            desc="applikationsform (eng: administration route)",
            type_cast=None,
            lov_params=LovGenContainer(
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
        db_obj.append(darrform_field)
        db_obj.extend(darrform_field_lov_items)

        ## hersteller
        darrform_field, darrform_field_lov_items = await self.generate_field(
            name="hersteller",
            desc="hersteller (eng: producer)",
            type_cast=None,
            lov_params=LovGenContainer(
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
        db_obj.append(darrform_field)
        db_obj.extend(darrform_field_lov_items)
        return db_obj

    async def get_drug_data_set(self) -> DrugDataSetVersion:
        return DrugDataSetVersion(
            dataset_version=self.dataset_name,
            dataset_name=self.dataset_name,
            dataset_link=self.dataset_link,
        )

    async def generate_field(
        self,
        name: str,
        desc=None,
        type_cast: ValueCastingFunc = None,
        lov_params: LovGenContainer = None,
    ) -> Tuple[DrugExtraFieldDefinition, List[DrugExtraFieldDefinitionLovItem]]:
        field = DrugExtraFieldDefinition(
            field_name=name,
            field_desc=desc,
            type=type_cast,
            has_list_of_values=False if lov_params is None else True,
        )
        return field, await self.generate_lov_items(field, lov_params)

    async def generate_lov_items(
        self, paren_field: DrugExtraField, lov_params: LovGenContainer
    ) -> List[DrugExtraFieldDefinitionLovItem]:
        # darrform_txt_headers = ["Dateiversion", "Datenstand", "darrform", "bedeutung"]
        lov_items: List[DrugExtraFieldDefinitionLovItem] = []
        with open(Path(self.source_dir, lov_params.lov_source_file)) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for index, row in enumerate(csvreader):
                value = row[
                    lov_params.lov_source_headers.index(lov_params.values_col_name)
                ]
                display_value = row[
                    lov_params.lov_source_headers.index(
                        lov_params.display_value_col_name
                    )
                ]
                li = DrugExtraFieldDefinitionLovItem(
                    field=paren_field,
                    value=value,
                    display_value=display_value,
                    sort_order=index,
                )
                lov_items.append(li)
        return lov_items
