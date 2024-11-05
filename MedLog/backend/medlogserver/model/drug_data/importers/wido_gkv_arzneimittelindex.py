from typing import List, Callable, Tuple, Dict, Optional, AsyncIterator, TypeVar
from pathlib import Path
import datetime
import csv
from dataclasses import dataclass
from sqlmodel import SQLModel, select
from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugAttr, DrugRefAttr
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    ValueTypeCasting,
    CustomPreParserFunc,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
    DrugAttrFieldLovItemCREATE,
)

from medlogserver.model.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug import Drug
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.log import get_logger
from medlogserver.config import Config

config = Config()
log = get_logger()


@dataclass
class WiDoDrugAttrFieldLovImportDefinition:
    lov_source_file: Optional[str]
    lov_source_col_headers: List[str]
    values_col_name: str
    display_value_col_name: str


@dataclass
class DrugAttrLovFieldDefinitionContainer:
    field: DrugAttrFieldDefinition
    lov: Optional[WiDoDrugAttrFieldLovImportDefinition] = None


@dataclass
class StammCol:
    name: str
    map2: Optional[str] = None
    cast_func: Optional[Callable] = None


stamm_col_definitions = [
    StammCol("dateiversion", map2=None),
    StammCol("datenstand", map2=None),
    StammCol("laufnr", map2=None),
    StammCol("stakenn", map2=None),
    StammCol("staname", map2=None),
    StammCol("atc_code", map2="code.ATC"),
    StammCol("indgr", map2="attr.indikationsgruppe"),
    StammCol("pzn", map2="code.PZN"),
    StammCol("name", map2="trade_name"),
    StammCol("hersteller_code", map2="ref_attr.hersteller"),
    StammCol("darrform", map2="ref_attr.darreichungsform"),
    StammCol("zuzahlstufe", map2="ref_attr.normpackungsgroesse"),
    StammCol("packgroesse", map2="attr.packgroesse"),
    StammCol("dddpk", map2="attr.ddd"),
    StammCol("apopflicht", map2="ref_attr.apopflicht"),
    StammCol("preisart_alt", map2=None),
    StammCol("preisart_neu", map2=None),
    StammCol("preis_alt", map2=None),
    StammCol("preis_neu", map2=None),
    StammCol("festbetrag", map2=None),
    StammCol(
        "marktzugang",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%Y%m%d").date(),
    ),
    StammCol(
        "ahdatum",
        map2="market_exit_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%Y%m%d").date(),
    ),
    StammCol("RÜCKRUF", map2=None),
    StammCol("GENERIKAKENN", map2=None),
    StammCol("APPFORM", map2=None),
    StammCol("BIOSIMILAR", map2=None),
    StammCol("ORPHAN", map2=None),
    # todo: continue here with the stamm columns
]


apopflicht_values = [
    DrugAttrFieldLovItemCREATE(value="0", display="Nichtarzneimittel", sort_order=0),
    DrugAttrFieldLovItemCREATE(
        value="1", display="nicht apothekenpflichtiges Arzneimittel", sort_order=1
    ),
    DrugAttrFieldLovItemCREATE(
        value="2",
        display="apothekenpflichtiges, rezeptfreies Arzneimittel",
        sort_order=2,
    ),
    DrugAttrFieldLovItemCREATE(
        value="3",
        display="rezeptpflichtiges Arzneimittel",
        sort_order=3,
    ),
]


class WidoAiImporter52(DrugDataSetImporterBase):
    def __init__(self):

        self.dataset_name = "Wido GKV Arzneimittelindex"
        self.api_name = "WidoAiDrug"
        self.dataset_link = (
            "https://www.wido.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        )
        self.source_dir = None
        self.version = None
        self._attr_definitons = None
        self._ref_attr_definitions = None
        self._code_definitions = None

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
        field_def_containers = await self._get_ref_attr_definitons()
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
        code_def = await self._get_code_definitions()
        if by_id:
            return [codes_def for codes_def in code_def if codes_def.id == by_id]
        return code_def

    async def _get_code_definitions(self):
        if self._code_definitions is not None:
            return self._code_definitions
        codes_defs = [
            DrugCodeSystem(
                id="ATC",
                name="ATC-Code (Klassifikation nach WIdO)",
                country="Germany",
                desc="ATC-Klassifikation des GKV-Arzneimittelindex mit ATC-Code,ATC-Bedeutung",
                optional=True,
                unique=False,
            ),
            DrugCodeSystem(
                id="PZN",
                name="Pharmazentralnummer",
                country="Germany",
                optional=False,
                unique=True,
            ),
        ]
        self._code_definitions = codes_defs
        return codes_defs

    def debug_count_field_def(self, objs) -> int:
        count = 0
        for obj in objs:
            if isinstance(obj, DrugAttrFieldDefinition):
                count += 1
        return count

    async def run_import(self, source_dir: Path, version: str):
        # generate schema definitions; fields,lov-defintions,...
        log.info("[DRUG DATA IMPORT] Parse metadata...")
        all_objs = []
        drug_dataset = await self._ensure_drug_dataset_version()
        # generate list of values
        lov_field_objects = await self._get_ref_attr_definitons()
        for field_name, lov_field_obj in lov_field_objects.items():
            all_objs.extend(
                await self._generate_lov_items(
                    lov_field_obj.field, lov_definition=lov_field_obj.lov
                )
            )
        # read all drugs with attributes
        async for obj in self._parse_wido_stamm_data(drug_dataset):
            all_objs.append(obj)

        # write everything to database
        await self.commit(all_objs)

    async def _parse_wido_stamm_data(
        self, drug_dataset_version: DrugDataSetVersion
    ) -> AsyncIterator[Drug | DrugAttr | DrugRefAttr | DrugCode]:
        log.info("[DRUG DATA IMPORT] Parse drug data...")
        with open(Path(self.source_dir, "stamm.txt")) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for row_index, row in enumerate(csvreader):
                if (
                    config.DRUG_DATA_IMPORT_MAX_ROWS
                    and row_index > config.DRUG_DATA_IMPORT_MAX_ROWS
                ):
                    return
                drug = Drug(source_dataset_id=drug_dataset_version.id)
                yield drug
                for col_index, col_def in enumerate(stamm_col_definitions):
                    if col_def.map2:
                        drug_attr = await self._parse_wido_stamm_row_value(
                            drug, row_val=row[col_index], col_def=col_def
                        )
                        if drug_attr is not None:
                            yield drug_attr

    async def _parse_wido_stamm_row_value(
        self, parent_drug: Drug, row_val: str, col_def: StammCol
    ) -> DrugAttr | DrugRefAttr | DrugCode | None:
        if "." in col_def.map2:
            field_type, field_name = col_def.map2.split(".", 1)
        else:
            field_type = None
            field_name = col_def.map2
        if row_val == "" or row_val is None:
            return
            # empty string are handled as null/None
        if col_def.cast_func is not None:
            row_val = col_def.cast_func(row_val)
        if field_type == "attr":
            field_defs = await self.get_attr_field_definitions(by_name=field_name)

            field_def: DrugAttrFieldDefinition = field_defs[0]
            if field_def.pre_parser and row_val:
                row_val = field_def.pre_parser.value(row_val)
            return DrugAttr(
                drug_id=parent_drug.id, field_name=field_name, value=row_val
            )
        elif field_type == "ref_attr":
            field_defs = await self.get_ref_attr_field_definitions(by_name=field_name)
            field_def: DrugAttrFieldDefinition = field_defs[0]
            if field_def.pre_parser:
                row_val = field_def.pre_parser.value(row_val)
            return DrugRefAttr(
                drug_id=parent_drug.id, field_name=field_name, value=row_val
            )
        elif field_type == "code":
            code_systems = await self.get_code_definitions(by_id=field_name)
            code_system: DrugCodeSystem = code_systems[0]
            return DrugCode(
                drug_id=parent_drug.id, code_system_id=code_system.id, code=row_val
            )
        else:
            if field_type is not None:
                raise AssertionError(f"field_type is {field_type}")
            # its a drug root attr.
            setattr(parent_drug, field_name, row_val)
            return

    async def commit(self, objs):
        async with get_async_session_context() as session:
            for obj in objs:
                session.add(obj)
            log.info(
                "[DRUG DATA IMPORT] Commit Drug data to database. This may take a while..."
            )
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
        if self._attr_definitons is not None:
            return self._attr_definitons
        self._attr_definitons = [
            DrugAttrFieldDefinition(
                field_name="packgroesse",
                field_name_display="Packungsgröße",
                field_desc="Packungsgröße (in 1/10 Einheiten)",
                type=ValueTypeCasting.INT,
                value_has_reference_list=False,
                examples=[1000],
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            DrugAttrFieldDefinition(
                field_name="indikationsgruppe",
                field_name_display="Indikationsgruppe",
                field_desc="Indikationsgruppe (nach Roter Liste 2014)",
                type=ValueTypeCasting.INT,
                value_has_reference_list=False,
                examples=[20],
                importer_name=self.__class__.__name__,
            ),
            DrugAttrFieldDefinition(
                field_name="marktzugang",
                field_name_display="Marktzugang",
                field_desc="Datum des Marktzugang",
                type=ValueTypeCasting.DATE,
                pre_parser=CustomPreParserFunc.WIDO_GKV_DATE,
                value_has_reference_list=False,
                examples=[],
                importer_name=self.__class__.__name__,
            ),
            DrugAttrFieldDefinition(
                field_name="ddd",
                field_name_display="Defined Daily Dose (DDD)",
                field_desc="DDD je Packung (nach WIdO, in 1/1000 Einheiten)",
                type=ValueTypeCasting.INT,
                value_has_reference_list=False,
                examples=[100],
                importer_name=self.__class__.__name__,
            ),
        ]
        #
        return self._attr_definitons

    async def _get_ref_attr_definitons(
        self,
    ) -> Dict[str, DrugAttrLovFieldDefinitionContainer]:
        if self._ref_attr_definitions is not None:
            return self._ref_attr_definitions

        fields = {}
        fields["darreichungsform"] = DrugAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="darreichungsform",
                field_name_display="Darreichungsform",
                field_desc="Wirkstoffhaltige Zubereitung, die dem Patienten verabreicht wird und die präsentierte Arzneiform (eng: dosage form)",
                type=ValueTypeCasting.STR,
                value_has_reference_list=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=WiDoDrugAttrFieldLovImportDefinition(
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
                field_name_display="Applikationsform",
                field_desc="Die Art und Weise bezeichnet, wie ein Arzneimittel verabreicht wird (eng: administration route)",
                type=ValueTypeCasting.STR,
                value_has_reference_list=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=WiDoDrugAttrFieldLovImportDefinition(
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
                field_name_display="Hersteller",
                field_desc="hersteller (eng: producer)",
                type=ValueTypeCasting.STR,
                value_has_reference_list=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=WiDoDrugAttrFieldLovImportDefinition(
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
                field_name_display="Normpackungsgröße",
                field_desc="Normpackungsgröße https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Packungsgroessen/_node.html",
                type=ValueTypeCasting.STR,
                value_has_reference_list=True,
                importer_name=self.__class__.__name__,
            ),
            lov=WiDoDrugAttrFieldLovImportDefinition(
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
                field_name_display="Apotheken-/Rezeptpflicht",
                field_desc="",
                type=ValueTypeCasting.INT,
                value_has_reference_list=True,
                importer_name=self.__class__.__name__,
            ),
            lov=apopflicht_values,
        )
        self._ref_attr_definitions = fields
        return fields

    async def _generate_lov_items(
        self,
        paren_field: DrugRefAttr,
        lov_definition: (
            WiDoDrugAttrFieldLovImportDefinition | List[DrugAttrFieldLovItemCREATE]
        ),
    ) -> List[DrugAttrFieldLovItem]:
        lov_items: List[DrugAttrFieldLovItem] = []
        if isinstance(lov_definition, WiDoDrugAttrFieldLovImportDefinition):

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
                        field_name=paren_field.field_name,
                        value=value,
                        display=display_value,
                        sort_order=index,
                    )
                    lov_items.append(li)
        elif isinstance(lov_definition, list):
            for li in lov_definition:
                lov_items.append(
                    DrugAttrFieldLovItem(
                        field_name=paren_field.field_name, **li.model_dump()
                    )
                )

        return lov_items
