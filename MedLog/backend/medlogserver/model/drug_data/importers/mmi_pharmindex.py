from typing import List, Callable, Tuple, Dict, Optional, AsyncIterator, TypeVar
from pathlib import Path
import datetime
import csv
from dataclasses import dataclass
from sqlmodel import SQLModel, select
from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugVal, DrugValRef
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
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.log import get_logger
from medlogserver.config import Config

config = Config()
log = get_logger()


@dataclass
class MmiPiDrugRefAttrFieldLovImportDefinition:
    lov_source_file: Optional[str] = "CATALOGENTRY.CSV"
    values_col_name: Optional[str] = "CODE"
    display_value_col_name: Optional[str] = "NAME"
    filter_col: Optional[str] = "CATALOGID"
    filter_val: Optional[str] = None


@dataclass
class DrugRefAttrLovFieldDefinitionContainer:
    field: DrugAttrFieldDefinition
    lov: Optional[MmiPiDrugRefAttrFieldLovImportDefinition] = None


@dataclass
class SourceAttrMapping:
    filename: str
    colname: str
    map2: Optional[str] = None
    cast_func: Optional[Callable] = None
    productid_ref_path: Optional[str] = (
        None  # if a mmi source table has no direkt product id we need path to map the product id. must start with  a column from the "filename" csv file and end with PRODUCT ID. e.g. "ITEM_ATC.CSV[ITEMID]/ITEM.CSV[ID]>[PRODUCTID]"
    )


mmi_rohdaten_r3_mapping = [
    SourceAttrMapping("PACKAGE.CSV", "NAME", map2="trade_name"),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "ONMARKETDATE",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").date(),
    ),
    ## FileProductMapping(map2="market_exit_date"), # exited drugs are in an extra file :/ we will fix that later
    # codes
    SourceAttrMapping("PACKAGE.CSV", "PZN", map2="codes.PZN"),
    SourceAttrMapping("PRODUCT.CSV", "ID", map2="codes.mmi_productid"),
    SourceAttrMapping("PRODUCT_ICD.CSV", "ICD-10", map2="codes.icd10"),
    SourceAttrMapping(
        "ITEM_ATC.CSV",
        "ATCCODE",
        map2="codes.ATC",
        productid_ref_path="ITEM_ATC.CSV[ITEMID]/ITEM.CSV[ID]>[PRODUCTID]",
    ),
    # attrs
    SourceAttrMapping(
        "ARV_PACKAGEGROUP.CSV",
        "DDDAMOUNT",
        map2="attrs.ddd",
        productid_ref_path="ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "CONTRACEPTIVE_FLAG",
        map2="attrs.ist_verhuetungsmittel",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "COSMETICS_FLAG",
        map2="attrs.ist_kosmetikum",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "DIETARYSUPPLEMENT_FLAG",
        map2="attrs.ist_nahrungsergaenzungsmittel",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HERBAL_FLAG",
        map2="attrs.ist_pflanzlich",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "GENERIC_FLAG",
        map2="attrs.ist_generikum",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HOMOEOPATHIC_FLAG",
        map2="attrs.ist_homoeopathisch",
    ),
    # ref attrs
    SourceAttrMapping(
        "PACKAGE.CSV",
        "IFAPHARMFORMCODE",
        map2="ref_attrs.darreichungsform",  # Im Vertrieb, Rückruf,... catalog ref id 109
    ),
    SourceAttrMapping(
        "ITEM.CSV",
        "ITEMROACODE",
        map2="ref_attrs.applikationsart",  # Im Vertrieb, Rückruf,... catalog ref id 123
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "SALESSTATUSCODE",
        map2="ref_attrs.vertriebsstatus",  # Im Vertrieb, Rückruf,... catalog ref id 116
    ),
    SourceAttrMapping(
        "PACKAGE.CSV",
        "PACKAGENORMSIZECODE",
        map2="ref_attrs.normgroesse",  # N0, N1,... catalog ref id 117
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "DISPENSINGTYPECODE",
        map2="ref_attrs.abgabestatus",  # rezeptpflichtig, apothenkenpflichtig,... catalog ref id 119
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTFOODTYPECODE",
        map2="ref_attrs.lebensmittel",  # ja, nein, sonstiges ,... catalog ref id 205
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTDIETETICSTYPECODE",
        map2="ref_attrs.diaetetikum",  # ja, nein, sonstiges ,... catalog ref id 206
    ),
    SourceAttrMapping(
        "PRODUCT_COMPANY.CSV",
        "COMPANYID",
        map2="ref_attrs.hersteller",
    ),
    # multi ref attrs
    SourceAttrMapping(
        "PRODUCT_KEYWORD.CSV",
        "CODE",
        map2="ref_multi_attrs.keywords",  # no catalog id. seperate csv named KEYWORD.CSV
    ),
]

code_attr_definitions = [
    DrugCodeSystem(
        id="ATC",
        name="ATC (nach DIMDI)",
        country="Germany",
        desc="Anatomisch-therapeutisch-chemische Klassifikation, die Erstellung erfolgt unter Verwendung der amtlichen Fassung der ATC-Klassifikation des Deutschen Instituts für Medizinische Dokumentation und Information (DIMDI)",
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
    DrugCodeSystem(
        id="ICD10",
        name="ICD-10",
        country="International",
        desc="Einordnung der Präparate nach ICD-10-Schlüsseln",
        optional=False,
        unique=True,
    ),
    DrugCodeSystem(
        id="MMI",
        name="MMI Product ID",
        country="Internal",
        desc="Interne 'PRODUCTID' des Vidal MMI Pharmindex",
        optional=False,
        unique=True,
    ),
]
importername = "MmmiPharmaindex1_32"
attr_definitions = [
    DrugAttrFieldDefinition(
        field_name="ddd",
        field_name_display="DDD",
        field_desc="Angenommene Mittlere Tagesdosis (Defined Daily Dose)",
        type=ValueTypeCasting.INT,
        optional=True,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[3],
        importer_name=importername,
        searchable=False,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_verhuetungsmittel",
        field_name_display="Verhütungsmittel",
        field_desc="Ist das Produkt ein Verhütungsmittel",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[True, False],
        importer_name=importername,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_kosmetikum",
        field_name_display="Kosmetikum",
        field_desc="Ist das Produkt ein Kosmetikum",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[True, False],
        importer_name=importername,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_nahrungsergaenzungsmittel",
        field_name_display="Nahrungsergänzungsmittel",
        field_desc="Ist das Produkt ein Nahrungsergänzungsmittel",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[True, False],
        importer_name=importername,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_pflanzlich",
        field_name_display="Pflanzlich",
        field_desc="Ist das Produkt Pflanzlich",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[True, False],
        importer_name=importername,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_generikum",
        field_name_display="Generikum",
        field_desc="Ist das Produkt ein Generikum",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[1, 0],
        importer_name=importername,
    ),
    DrugAttrFieldDefinition(
        field_name="ist_homoeopathisch",
        field_name_display="Homöopathisch",
        field_desc="Ist das Produkt Homöopathisch",
        type=ValueTypeCasting.BOOL,
        optional=False,
        default=False,
        is_reference_list_field=False,
        is_multi_val_field=False,
        examples=[1, 0],
        importer_name=importername,
    ),
]

multi_attr_definitions: List[DrugRefAttrLovFieldDefinitionContainer] = []

# ref values packed together into a tuple with ref LOV import data
ref_attr_definitions: List[DrugRefAttrLovFieldDefinitionContainer] = [
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="darreichungsform",
            field_name_display="Darreichungsform",
            field_desc="Darreichungsform IFA",
            type=ValueTypeCasting.STR,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["AUGEN", "DIL"],
            importer_name=importername,
            searchable=True,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="109",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="applikationsart",
            field_name_display="Applikationsart",
            field_desc="Art und Weise wie ein Arzneimittel verabreicht wird",
            type=ValueTypeCasting.INT,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["104", "19"],
            importer_name=importername,
            searchable=True,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="123",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="vertriebsstatus",
            field_name_display="Vertriebsstatus",
            field_desc="Wird das Produkt momentan vertrieben",
            type=ValueTypeCasting.STR,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["D", "F"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="116",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="normgroesse",
            field_name_display="Normgrösse",
            field_desc="Packungsgrößenkennzeichnung für Medikamente ist eine in Deutschland bestehende Normierung der in der Apotheke abzugebenden Menge",
            type=ValueTypeCasting.STR,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["A", "1"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="117",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="abgabestatus",
            field_name_display="Abgabestatus",
            field_desc="Ob und wie das Produkt an den Patienten abgegeben werden darf",
            type=ValueTypeCasting.INT,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["0", "2"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="119",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="lebensmittel",
            field_name_display="Lebensmittel",
            field_desc="Lebensmittelstatus des Produkt",
            type=ValueTypeCasting.STR,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["E", "N", "Y"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="205",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="diaetetikum",
            field_name_display="Diätetikum",
            field_desc="Diaetetikumstatus des Produkt",
            type=ValueTypeCasting.STR,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["E", "N", "Y"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="206",
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="hersteller",
            field_name_display="Hersteller",
            field_desc="Hersteller des Produkt",
            type=ValueTypeCasting.STR,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=["13819", "15777", "12"],
            importer_name=importername,
            searchable=False,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            lov_source_file="COMPANY.CSV",
            values_col_name="ID",
            display_value_col="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
]

# ref values packed together into a tuple with ref LOV import data
multi_ref_attr_definitions: List[DrugRefAttrLovFieldDefinitionContainer] = [
    DrugRefAttrLovFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="keywords",
            field_name_display="Stichwörter",
            field_desc="Stichwörter",
            type=ValueTypeCasting.INT,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=True,
            examples=[["8", "23"], ["70"]],
            importer_name=importername,
            searchable=True,
        ),
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            lov_source_file="KEYWORD.CSV",
            values_col_name="ID",
            display_value_col="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
]


class MmmiPharmaindex1_32(DrugDataSetImporterBase):
    def __init__(self):

        self.dataset_name = "MmiPi GKV Arzneimittelindex"
        self.api_name = "WidoAiDrug"
        self.dataset_link = "https://www.MmiPi.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        self.source_dir = None
        self.version = None
        self._attr_definitions = None
        self._ref_attr_definitions = None
        self._code_definitions = None

    async def get_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                field_def
                for field_def in attr_definitions
                if field_def.field_name == by_name
            ]
        return attr_definitions

    async def get_attr_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                field_def.field
                for field_def in ref_attr_definitions
                if field_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in ref_attr_definitions]

    async def get_attr_multi_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                field_def.field
                for field_def in multi_attr_definitions
                if field_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in multi_attr_definitions]

    async def get_attr_multi_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                field_def.field
                for field_def in multi_ref_attr_definitions
                if field_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in multi_ref_attr_definitions]

    async def get_code_definitions(
        self, by_id: Optional[str] = None
    ) -> List[DrugCodeSystem]:
        return code_attr_definitions

    def debug_count_field_def(self, objs) -> int:
        count = 0
        for obj in objs:
            if isinstance(obj, DrugAttrFieldDefinition):
                count += 1
        return count

    ## you are here
    async def run_import(self, source_dir: Path, version: str):
        # generate schema definitions; fields,lov-defintions,...
        log.info("[DRUG DATA IMPORT] Parse metadata...")
        all_objs = []
        drug_dataset = await self._ensure_drug_dataset_version()
        # generate list of values
        lov_field_objects = await self._get_ref_attr_definitions()
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
    ) -> AsyncIterator[DrugData | DrugVal | DrugValRef | DrugCode]:
        log.info("[DRUG DATA IMPORT] Parse drug data...")
        with open(Path(self.source_dir, "stamm.txt")) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for row_index, row in enumerate(csvreader):
                if (
                    config.DRUG_DATA_IMPORT_MAX_ROWS
                    and row_index > config.DRUG_DATA_IMPORT_MAX_ROWS
                ):
                    return
                drug = DrugData(source_dataset_id=drug_dataset_version.id)
                yield drug
                for col_index, col_def in enumerate(stamm_col_definitions):
                    if col_def.map2:
                        drug_attr = await self._parse_wido_stamm_row_value(
                            drug, row_val=row[col_index], col_def=col_def
                        )
                        if drug_attr is not None:
                            yield drug_attr

    async def _parse_wido_stamm_row_value(
        self, parent_drug: DrugData, row_val: str, col_def: SourceAttrMapping
    ) -> DrugVal | DrugValRef | DrugCode | None:
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
            return DrugVal(drug_id=parent_drug.id, field_name=field_name, value=row_val)
        elif field_type == "ref_attr":
            field_defs = await self.get_attr_ref_field_definitions(by_name=field_name)
            field_def: DrugAttrFieldDefinition = field_defs[0]
            if field_def.pre_parser:
                row_val = field_def.pre_parser.value(row_val)
            return DrugValRef(
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

    async def _get_attr_definitions(self) -> List[DrugAttrFieldDefinition]:
        """
            packgroesse: Optional[int] = Field(
            default=None,
            description="Packungsgröße (in 1/10 Einheiten)",
            sa_type=Integer,
            sa_column_kwargs={"comment": "gkvai_source_csv_col_index:12"},
            schema_extra={"examples": ["1000"]},
        )
        """
        if self._attr_definitions is not None:
            return self._attr_definitions
        self._attr_definitions = [
            DrugAttrFieldDefinition(
                field_name="packgroesse",
                field_name_display="Packungsgröße",
                field_desc="Packungsgröße (in 1/10 Einheiten)",
                type=ValueTypeCasting.INT,
                is_reference_list_field=False,
                examples=[1000],
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            DrugAttrFieldDefinition(
                field_name="indikationsgruppe",
                field_name_display="Indikationsgruppe",
                field_desc="Indikationsgruppe (nach Roter Liste 2014)",
                type=ValueTypeCasting.INT,
                is_reference_list_field=False,
                examples=[20],
                importer_name=self.__class__.__name__,
            ),
            DrugAttrFieldDefinition(
                field_name="marktzugang",
                field_name_display="Marktzugang",
                field_desc="Datum des Marktzugang",
                type=ValueTypeCasting.DATE,
                pre_parser=CustomPreParserFunc.WIDO_GKV_DATE,
                is_reference_list_field=False,
                examples=[],
                importer_name=self.__class__.__name__,
            ),
            DrugAttrFieldDefinition(
                field_name="ddd",
                field_name_display="Defined Daily Dose (DDD)",
                field_desc="DDD je Packung (nach MmiPi, in 1/1000 Einheiten)",
                type=ValueTypeCasting.INT,
                is_reference_list_field=False,
                examples=[100],
                importer_name=self.__class__.__name__,
            ),
        ]
        #
        return self._attr_definitions

    async def _get_ref_attr_definitions(
        self,
    ) -> Dict[str, DrugRefAttrLovFieldDefinitionContainer]:
        if self._ref_attr_definitions is not None:
            return self._ref_attr_definitions

        fields = {}
        fields["darreichungsform"] = DrugRefAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="darreichungsform",
                field_name_display="Darreichungsform",
                field_desc="Wirkstoffhaltige Zubereitung, die dem Patienten verabreicht wird und die präsentierte Arzneiform (eng: dosage form)",
                type=ValueTypeCasting.STR,
                is_reference_list_field=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=MmiPiDrugRefAttrFieldLovImportDefinition(
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
        fields["applikationsform"] = DrugRefAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="applikationsform",
                field_name_display="Applikationsform",
                field_desc="Die Art und Weise bezeichnet, wie ein Arzneimittel verabreicht wird (eng: administration route)",
                type=ValueTypeCasting.STR,
                is_reference_list_field=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=MmiPiDrugRefAttrFieldLovImportDefinition(
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
        fields["hersteller"] = DrugRefAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="hersteller",
                field_name_display="Hersteller",
                field_desc="hersteller (eng: producer)",
                type=ValueTypeCasting.STR,
                is_reference_list_field=True,
                importer_name=self.__class__.__name__,
                searchable=True,
            ),
            lov=MmiPiDrugRefAttrFieldLovImportDefinition(
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
        fields["normpackungsgroesse"] = DrugRefAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="normpackungsgroesse",
                field_name_display="Normpackungsgröße",
                field_desc="Normpackungsgröße https://www.bfarm.de/DE/Arzneimittel/Arzneimittelinformationen/Packungsgroessen/_node.html",
                type=ValueTypeCasting.STR,
                is_reference_list_field=True,
                importer_name=self.__class__.__name__,
            ),
            lov=MmiPiDrugRefAttrFieldLovImportDefinition(
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
        fields["apopflicht"] = DrugRefAttrLovFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="apopflicht",
                field_name_display="Apotheken-/Rezeptpflicht",
                field_desc="",
                type=ValueTypeCasting.INT,
                is_reference_list_field=True,
                importer_name=self.__class__.__name__,
            ),
            lov=apopflicht_values,
        )
        self._ref_attr_definitions = fields
        return fields

    async def _generate_lov_items(
        self,
        paren_field: DrugValRef,
        lov_definition: (
            MmiPiDrugRefAttrFieldLovImportDefinition | List[DrugAttrFieldLovItemCREATE]
        ),
    ) -> List[DrugAttrFieldLovItem]:
        lov_items: List[DrugAttrFieldLovItem] = []
        if isinstance(lov_definition, MmiPiDrugRefAttrFieldLovImportDefinition):

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
