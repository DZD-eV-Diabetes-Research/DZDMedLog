from typing import List, Callable, Tuple, Dict, Optional
from pathlib import Path
import csv
from dataclasses import dataclass

from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugAttr
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    ValueTypeCasting,
    CustomParserFunc,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
)

from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug import Drug
from medlogserver.model.drug_data.drug_code import DrugCode


@dataclass
class DrugAttrFieldLovImportDefinition:
    lov_source_file: Optional[str]
    lov_source_col_headers: List[str]
    values_col_name: str
    display_value_col_name: str


@dataclass
class DrugAttrLovFieldDefinitionContainer:
    field: DrugAttrFieldDefinition
    lov: Optional[DrugAttrFieldLovImportDefinition] = None


@dataclass
class StammCol:
    name: str
    map2: Optional[str]


stamm_col_definitions = [
    StammCol("dateiversion", map2=None, desc="Dateiversion"),
    StammCol("datenstand", map2=None, desc="Monat Datenstand (JJJJMM)"),
    StammCol("stakenn", map2=None),
    StammCol("staname", map2=None),
    StammCol("atc_code", map2="code.ATC-WiDo"),
    StammCol("indgr", map2="attr.indikationsgruppe"),
    StammCol("pzn", map2="code.PZN"),
    StammCol("name", map2="trade_name"),
    StammCol("hersteller_code", map2="ref_attr.hersteller"),
    StammCol("darrform", map2="ref_attr.darreichungsform"),
    StammCol("zuzahlstufe", map2="ref_attr.normpackungsgroesse"),
    StammCol("packgroesse", map2="attr.packgroesse"),
    StammCol("dddpk", map2=None),
    StammCol("apopflicht", map2="ref_attr.apopflicht"),
    StammCol("preisart_alt", map2=None),
    StammCol("preisart_neu", map2=None),
    StammCol("preis_alt", map2=None),
    StammCol("preis_neu", map2=None),
    StammCol("festbetrag", map2=None),
    StammCol("marktzugang", map2=None),
    # todo: continue here with the stamm columns
]


apopflicht_values = [
    DrugAttrFieldLovItem(value="0", display="Nichtarzneimittel", sort_order=0),
    DrugAttrFieldLovItem(
        value="1", display="nicht apothekenpflichtiges Arzneimittel", sort_order=1
    ),
    DrugAttrFieldLovItem(
        value="2",
        display="apothekenpflichtiges, rezeptfreies Arzneimittel",
        sort_order=2,
    ),
]


class WidoAiImporter(DrugDataSetImporterBase):
    def __init__(self, source_dir: Path, version: str):

        self.dataset_name = "Wido GKV Arzneimittelindex"
        self.api_name = "WidoAiDrug"
        self.dataset_link = (
            "https://www.wido.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        )
        self.source_dir = source_dir
        self.version = version

    async def get_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        field_def_containers = await self._get_attr_definitons()
        if by_name:
            return [
                field_def
                for field_def in field_def_containers
                if field_def.field_name == by_name
            ]
        return field_def_containers
        return [field_cont.field for name, field_cont in field_def_containers.items()]

    async def get_ref_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        field_def_containers = await self._get_attr_definitons_with_lov()
        if by_name:
            return [
                field_cont.field
                for name, field_cont in field_def_containers.items()
                if name == by_name
            ]
        return [field_cont.field for name, field_cont in field_def_containers.items()]

    async def get_code_definitions(
        self, by_id: Optional[str] = None
    ) -> List[DrugCodeSystem]:
        codes_defs = [
            DrugCodeSystem(
                id="ATC-WiDo",
                name="Pharmazentralnummer",
                country="Germany",
                desc="ATC-Klassifikation des GKV-Arzneimittelindex mit ATC-Code,ATC-Bedeutung",
            ),
            DrugCodeSystem(
                id="ATC-Amtlich",
                name="Pharmazentralnummer",
                country="Germany",
                desc="Amtliche ATC-Klassifikation mit ATC-Code, ATC-Bedeutung",
            ),
            DrugCodeSystem(id="PZN", name="Pharmazentralnummer", country="Germany"),
        ]
        if by_id:
            return [codes_def for codes_def in codes_defs if codes_def.id == by_id]
        return codes_defs

    async def run_import(self):
        field_objs = await self._get_attr_definitons()

        lov_field_objects = await self._get_attr_definitons_with_lov()
        for field_name, lov_field_obj in lov_field_objects.items():
            field_objs.append(lov_field_obj.field)
            field_objs.extend(
                await self._generate_lov_items(
                    lov_field_obj.field, lov_definition=lov_field_obj.lov
                )
            )
        await self.commit(field_objs)

    async def _import_stamm(self):
        with open(Path(self.source_dir, "stamm.txt")) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for row_index, row in enumerate(csvreader):
                drug = Drug()
                for col_index, col_def in enumerate(stamm_col_definitions):
                    if col_def.map2:
                        drug_attr: DrugAttr | DrugCode = self._parse_stamm_row_value(
                            drug, row_val=row[col_index], col_def=col_def
                        )

    async def _parse_stamm_row_value(
        self, parent_drug: Drug, row_val: str, col_def: StammCol
    ) -> DrugAttr | DrugCode:

        field_type, field_name = col_def.map2.split(".", 1)
        if field_type == "attr":
            field_def: DrugAttrFieldDefinition = await self.get_attr_field_definitions(
                by_name=field_name
            )[0]
            if field_def.pre_parser:
                row_val = field_def.pre_parser.value(row_val)
            DrugAttr(parent_drug, field_name=field_name, value=row_val)

        pass

    async def commit(self, objs):
        async with get_async_session_context() as session:
            # todo: Write db crud classes to interact with database
            for obj in objs:
                # await session.merge(obj)
                pass
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
                field_display="Packungsgröße",
                field_desc="Packungsgröße (in 1/10 Einheiten)",
                type=ValueTypeCasting.INT,
                has_list_of_values=False,
                examples=[1000],
            ),
            DrugAttrFieldDefinition(
                field_name="indikationsgruppe",
                field_display="Indikationsgruppe",
                field_desc="Indikationsgruppe (nach Roter Liste 2014)",
                type=ValueTypeCasting.INT,
                has_list_of_values=False,
                examples=[20],
            ),
            DrugAttrFieldDefinition(
                field_name="marktzugang",
                field_display="Marktzugang",
                field_desc="Datum des Marktzugang",
                type=ValueTypeCasting.DATE,
                pre_parser=CustomParserFunc.WIDO_GKV_DATE,
                has_list_of_values=False,
                examples=[],
            ),
        )
        return fields

    async def _get_attr_definitons_with_lov(
        self,
    ) -> Dict[str, DrugAttrLovFieldDefinitionContainer]:
        fields = {}
        fields["darreichungsform"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="darreichungsform",
                field_display="Darreichungsform",
                field_desc="Wirkstoffhaltige Zubereitung, die dem Patienten verabreicht wird und die präsentierte Arzneiform (eng: dosage form)",
                type=ValueTypeCasting.STR,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovImportDefinition(
                lov_source_file="darrform.txt",
                lov_source_col_headers=[
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
                field_display="Applikationsform",
                field_desc="Die Art und Weise bezeichnet, wie ein Arzneimittel verabreicht wird (eng: administration route)",
                type=ValueTypeCasting.STR,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovImportDefinition(
                lov_source_file="applikationsform.txt",
                lov_source_col_headers=[
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
                field_display="Hersteller",
                field_desc="hersteller (eng: producer)",
                type=ValueTypeCasting.STR,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovImportDefinition(
                lov_source_file="hersteller.txt",
                lov_source_col_headers=[
                    "Dateiversion",
                    "Datenstand",
                    "herstellercode",
                    "bedeutung",
                ],
                values_col_name="herstellercode",
                display_value_col_name="bedeutung",
            ),
        )
        fields["normpackungsgroesse"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="normpackungsgroesse",
                field_display="Normpackungsgröße",
                field_desc="Normpackungsgröße https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Packungsgroessen/_node.html",
                type=ValueTypeCasting.STR,
                has_list_of_values=True,
            ),
            lov=DrugAttrFieldLovImportDefinition(
                lov_source_file="normpackungsgroessen.txt",
                lov_source_col_headers=[
                    "Dateiversion",
                    "Datenstand",
                    "normpackungsgroessen_code",
                    "bedeutung",
                ],
                values_col_name="normpackungsgroessen_code",
                display_value_col_name="bedeutung",
            ),
        )
        fields["apopflicht"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="apopflicht",
                field_display="Apotheken-/Rezeptpflicht",
                field_desc="",
                type=ValueTypeCasting.INT,
                has_list_of_values=True,
            ),
            lov=apopflicht_values,
        )
        return fields

    async def _generate_lov_items(
        self,
        paren_field: DrugAttr,
        lov_definition: DrugAttrFieldLovImportDefinition | List[DrugAttrFieldLovItem],
    ) -> List[DrugAttrFieldLovItem]:
        lov_items: List[DrugAttrFieldLovItem] = []
        if isinstance(lov_definition, DrugAttrFieldLovImportDefinition):

            with open(Path(self.source_dir, lov_definition.lov_source_file)) as csvfile:
                csvreader = csv.reader(csvfile, delimiter=";")
                for index, row in enumerate(csvreader):
                    value = row[
                        lov_definition.lov_source_col_headers.index(
                            lov_definition.values_col_name
                        )
                    ]
                    display_value = row[
                        lov_definition.lov_source_col_headers.index(
                            lov_definition.display_value_col_name
                        )
                    ]
                    li = DrugAttrFieldLovItem(
                        field=paren_field,
                        value=value,
                        display=display_value,
                        sort_order=index,
                    )
                    lov_items.append(li)
        elif isinstance(lov_definition, list):
            for li in lov_definition:
                li.field = paren_field
            lov_items.append(li)

        return lov_items
