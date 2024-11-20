from typing import (
    List,
    Callable,
    Tuple,
    Dict,
    Optional,
    AsyncIterator,
    TypeVar,
    Any,
    Literal,
    Type,
    Union,
)
from pathlib import Path
import datetime
import csv
import re
from dataclasses import dataclass
from sqlmodel import SQLModel, select
from medlogserver.db._session import get_async_session_context

from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import (
    DrugModelTableBase,
    DrugVal,
    DrugValRef,
    DrugValMulti,
    DrugValMultiRef,
)
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
from medlogserver.model.unset import Unset
from medlogserver.utils import extract_bracket_values

config = Config()
log = get_logger()
importername = "MmmiPharmaindex1_32"


@dataclass
class MmiPiDrugAttrRefFieldLovImportDefinition:
    lov_source_file: Optional[str] = "CATALOGENTRY.CSV"
    values_col_name: Optional[str] = "CODE"
    display_value_col_name: Optional[str] = "NAME"
    filter_col: Optional[str] = "CATALOGID"
    filter_val: Optional[str] = None


@dataclass
class SourceAttrMapping:
    filename: str
    colname: str
    source_path: Optional[str] = (
        None  # CSVs files path from PACKAGE.CSV to the target row that contains the "colname" value
    )
    map2: str = None
    cast_func: Optional[Callable] = None
    filter_colname: str = None
    filter_colval: str = None

    @property
    def drug_attr_name(self) -> str:
        if "." not in self.map2:
            return self.map2
        return self.map2.split(".")[1]

    @property
    def drug_attr_type_name(
        self,
    ) -> Literal[
        "root", "attrs", "attrs_multi", "attrs_ref", "attrs_multi_ref", "codes"
    ]:
        if "." not in self.map2:
            return "root"
        return self.map2.split(".")[0]

    @property
    def drug_attr_type(
        self,
    ) -> Union[
        Type[DrugVal],
        Type[DrugValMulti],
        Type[DrugValRef],
        Type[DrugValMultiRef],
        Type[DrugCode],
    ]:
        t = self.drug_attr_type_name
        if t == "root":
            raise ValueError(
                f"[{self.__class__.__name__}] Drug data root attributes are just scalar value and do not have any container class/model"
            )
        map = {
            "attrs": DrugVal,
            "attrs_multi": DrugValMulti,
            "attrs_ref": DrugValRef,
            "attrs_multi_ref": DrugValMultiRef,
            "codes": DrugCode,
        }
        return map[t]


@dataclass
class DrugAttrFieldDefinitionContainer:
    field: DrugAttrFieldDefinition | DrugCodeSystem
    source_mapping: Optional[SourceAttrMapping]
    lov: Optional[MmiPiDrugAttrRefFieldLovImportDefinition] = None


mmi_rohdaten_r3_mappings = {
    "trade_name": SourceAttrMapping(
        "PACKAGE.CSV",
        "NAME",
        # source_path="PACKAGE.CSV[ID]",
        map2="trade_name",
    ),
    "market_access_date": SourceAttrMapping(
        "PACKAGE.CSV",
        "ONMARKETDATE",
        # source_path="PACKAGE.CSV[ID]",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").date(),
    ),
    ## FileProductMapping(map2="market_exit_date"), # exited drugs are in an extra file :/ we will fix that later
    # codes
    "codes.PZN": SourceAttrMapping(
        "PACKAGE.CSV",
        "PZN",
        # source_path="PACKAGE.CSV[ID]",
        map2="codes.PZN",
    ),
    "codes.MMIP": SourceAttrMapping(
        "PACKAGE.CSV",
        "PRODUCTID",
        # source_path="PACKAGE.CSV[ID]",
        map2="codes.MMIP",
    ),
    "codes.ATC": SourceAttrMapping(
        "ITEM_ATC.CSV",
        "ATCCODE",
        source_path="PACKAGE.CSV[PRODUCTID]/ITEM.CSV[PRODUCTID]>[ID]/ITEM_ATC.CSV[ITEMID]",
        map2="codes.ATC",
    ),
    # attrs
    "attrs.amount": SourceAttrMapping(
        "PACKAGE.CSV",
        "AMOUNTTEXT",
        # source_path="PACKAGE.CSV[ID]",
        map2="attrs.amount",
    ),
    "attrs.ist_verhuetungsmittel": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "CONTRACEPTIVE_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_verhuetungsmittel",
    ),
    "attrs.ist_kosmetikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "COSMETICS_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_kosmetikum",
    ),
    "attrs.ist_nahrungsergaenzungsmittel": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "DIETARYSUPPLEMENT_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_nahrungsergaenzungsmittel",
    ),
    "attrs.ist_pflanzlich": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HERBAL_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_pflanzlich",
    ),
    "attrs.ist_generikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "GENERIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_generikum",
    ),
    "attrs.ist_homoeopathisch": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HOMOEOPATHIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_homoeopathisch",
    ),
    "attrs_ref.darreichungsform":
    # ref attrs
    SourceAttrMapping(
        "PACKAGE.CSV",
        "IFAPHARMFORMCODE",
        # source_path="PACKAGE.CSV[ID]",
        map2="attrs_ref.darreichungsform",  # Im Vertrieb, Rückruf,... catalog ref id 109
    ),
    "attrs_ref.vertriebsstatus": SourceAttrMapping(
        "PACKAGE.CSV",
        "SALESSTATUSCODE",
        # source_path="PACKAGE.CSV[ID]",
        map2="attrs_ref.vertriebsstatus",  # Im Vertrieb, Rückruf,... catalog ref id 116
    ),
    "attrs_ref.normgroesse": SourceAttrMapping(
        "PACKAGE.CSV",
        "PACKAGENORMSIZECODE",
        # source_path="PACKAGE.CSV[ID]",
        map2="attrs_ref.normgroesse",  # N0, N1,... catalog ref id 117
    ),
    "attrs_ref.abgabestatus": SourceAttrMapping(
        "PRODUCT.CSV",
        "DISPENSINGTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.abgabestatus",  # rezeptpflichtig, apothenkenpflichtig,... catalog ref id 119
    ),
    "attrs_ref.lebensmittel": SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTFOODTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.lebensmittel",  # ja, nein, sonstiges ,... catalog ref id 205
    ),
    "attrs_ref.diaetetikum": SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTDIETETICSTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.diaetetikum",  # ja, nein, sonstiges ,... catalog ref id 206
    ),
    "attrs_ref.hersteller": SourceAttrMapping(
        "PRODUCT_COMPANY.CSV",
        "COMPANYID",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_COMPANY.CSV[PRODUCTID]",
        map2="attrs_ref.hersteller",
        filter_colname="PRODUCTCOMPANYTYPECODE",
        filter_colval="M",  # only "hersteller" no "mitvertriebler". other wise we get multiple hersteller per product
    ),
    # multi ref attrs
    "attrs_multi_ref.applikationsart": SourceAttrMapping(
        "ITEM.CSV",
        "ITEMROACODE",
        source_path="PACKAGE.CSV[PRODUCTID]/ITEM.CSV[PRODUCTID]",
        map2="attrs_multi_ref.applikationsart",  # Im Vertrieb, Rückruf,... catalog ref id 123
    ),
    "attrs_multi_ref.keywords": SourceAttrMapping(
        "PRODUCT_KEYWORD.CSV",
        "CODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_KEYWORD.CSV[PRODUCTID]",
        map2="attrs_multi_ref.keywords",  # no catalog id. seperate csv named KEYWORD.CSV
    ),
    "attrs_multi_ref.icd10": SourceAttrMapping(
        "PRODUCT_ICD.CSV",
        "ICDCODE",
        map2="attrs_multi_ref.icd10",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_ICD.CSV[PRODUCTID]",  # icd10 code,... catalog ref id 18
    ),
}

""" I can not grasp the DDD in mmi pharmindex. there is only a DDD per Arzneimittelvereinbarungen (AVR) but that makes no sense for me. Lets keep that stuff out for now.
    SourceAttrMapping(
        "ARV_PACKAGEGROUP.CSV",
        "DDDAMOUNT",
        packageid_path="ARV_PACKAGEGROUP.CSV[PACKAGEID]",
        map2="attrs.ddd",
    ),
"""

root_props_mapping = {
    prop_name: mapping
    for prop_name, mapping in mmi_rohdaten_r3_mappings.items()
    if not "." in prop_name
}

code_attr_definitions = [
    DrugAttrFieldDefinitionContainer(
        field=DrugCodeSystem(
            id="ATC",
            name="ATC (nach DIMDI)",
            country="Germany",
            desc="Anatomisch-therapeutisch-chemische Klassifikation, die Erstellung erfolgt unter Verwendung der amtlichen Fassung der ATC-Klassifikation des Deutschen Instituts für Medizinische Dokumentation und Information (DIMDI)",
            optional=True,
            unique=False,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["codes.ATC"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugCodeSystem(
            id="PZN",
            name="Pharmazentralnummer",
            country="Germany",
            optional=False,
            unique=True,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["codes.PZN"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugCodeSystem(
            id="MMIP",
            name="MMI Product ID",
            country="Internal",
            desc="Interne 'PRODUCTID' des Vidal MMI Pharmindex",
            optional=False,
            unique=False,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["codes.MMIP"],
    ),
]


attr_definitions = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="amount",
            field_name_display="Menge",
            field_desc="Menge in der Produktpackung",
            type=ValueTypeCasting.STR,
            optional=True,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=["3.5 g", "2x100 ml", "60 st"],
            importer_name=importername,
            searchable=False,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.amount"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_verhuetungsmittel",
            field_name_display="Verhütungsmittel",
            field_desc="Ist das Produkt ein Verhütungsmittel",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[True, False],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_verhuetungsmittel"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_kosmetikum",
            field_name_display="Kosmetikum",
            field_desc="Ist das Produkt ein Kosmetikum",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[True, False],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_kosmetikum"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_nahrungsergaenzungsmittel",
            field_name_display="Nahrungsergänzungsmittel",
            field_desc="Ist das Produkt ein Nahrungsergänzungsmittel",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[True, False],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_nahrungsergaenzungsmittel"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_pflanzlich",
            field_name_display="Pflanzlich",
            field_desc="Ist das Produkt Pflanzlich",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[True, False],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_pflanzlich"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_generikum",
            field_name_display="Generikum",
            field_desc="Ist das Produkt ein Generikum",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[1, 0],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_generikum"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="ist_homoeopathisch",
            field_name_display="Homöopathisch",
            field_desc="Ist das Produkt Homöopathisch",
            type=ValueTypeCasting.BOOL,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=[1, 0],
            importer_name=importername,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_homoeopathisch"],
    ),
]
""" I can not grasp the DDD in mmi pharmindex. there is only a DDD per Arzneimittelvereinbarungen (AVR) but that makes no sense for me. Lets keep that stuff out for now.
DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
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
"""

attr_multi_definitions: List[DrugAttrFieldDefinitionContainer] = []

# ref values packed together into a tuple with ref LOV import data
attr_ref_definitions: List[DrugAttrFieldDefinitionContainer] = [
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.darreichungsform"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="109",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.vertriebsstatus"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="116",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.normgroesse"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="117",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.abgabestatus"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="119",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.lebensmittel"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="205",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.diaetetikum"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="206",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.hersteller"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            lov_source_file="COMPANY.CSV",
            values_col_name="ID",
            display_value_col_name="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
]

# ref values packed together into a tuple with ref LOV import data
attr_multi_ref_definitions: List[DrugAttrFieldDefinitionContainer] = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="applikationsart",
            field_name_display="Applikationsart",
            field_desc="Art und Weise wie ein Arzneimittel verabreicht wird",
            type=ValueTypeCasting.INT,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=True,
            examples=["104", "19"],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs_multi_ref.applikationsart"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="123",
        ),
    ),
    DrugAttrFieldDefinitionContainer(
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
        source_mapping=mmi_rohdaten_r3_mappings["attrs_multi_ref.keywords"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            lov_source_file="KEYWORD.CSV",
            values_col_name="CODE",
            display_value_col_name="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="icd10",
            field_name_display="ICD-10 Codes",
            field_desc="Einordnung der Präparate nach ICD-10-Schlüssel",
            type=ValueTypeCasting.STR,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=True,
            examples=[["A01.0 M01.39", "B44.8 K23.8"], ["F41.1"]],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=mmi_rohdaten_r3_mappings["attrs_multi_ref.icd10"],
        lov=MmiPiDrugAttrRefFieldLovImportDefinition(
            filter_val="18",
        ),
    ),
]


class MmmiPharmaindex1_32(DrugDataSetImporterBase):
    def __init__(self):

        self.dataset_name = "MMI Pharmindex"
        self.api_name = "mmipharmindex"
        self.dataset_link = "https://www.MmiPi.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        self.source_dir = None
        self.version = None
        self._attr_definitions = None
        self._attr_ref_definitions = None
        self._code_definitions = None

    async def get_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                attr_def.field
                for attr_def in attr_definitions
                if attr_def.field.field_name == by_name
            ]
        return [attr_def.field for attr_def in attr_definitions]

    async def get_attr_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                attr_def.field
                for attr_def in attr_ref_definitions
                if attr_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in attr_ref_definitions]

    async def get_attr_multi_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                attr_def.field
                for attr_def in attr_multi_definitions
                if attr_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in attr_multi_definitions]

    async def get_attr_multi_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if by_name:
            return [
                field_def.field
                for field_def in attr_multi_ref_definitions
                if field_def.field.field_name == by_name
            ]
        return [field_def.field for field_def in attr_multi_ref_definitions]

    async def get_code_definitions(
        self, by_id: Optional[str] = None
    ) -> List[DrugCodeSystem]:
        if by_id:
            return [
                field_def.field
                for field_def in attr_multi_ref_definitions
                if field_def.field.field_name == by_id
            ]
        return [field_def.field for field_def in code_attr_definitions]

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
        attr_defs = attr_definitions + attr_multi_definitions
        all_objs.extend(attr_defs)
        for ref_lov_field_obj in attr_ref_definitions + attr_multi_ref_definitions:
            all_objs.append(ref_lov_field_obj.field)
            all_objs.extend(
                await self._generate_lov_items(
                    ref_lov_field_obj.field, lov_definition=ref_lov_field_obj.lov
                )
            )

        # read all drugs with attributes
        drug_data_objs = await self._parse_drug_data(drug_dataset)
        for obj in drug_data_objs:
            if hasattr(obj, "keywords") and obj.field_name == "keywords":
                print("KW", obj)
        all_objs.extend(drug_data_objs)

        # write everything to database
        await self.commit(all_objs)

    async def _parse_drug_data(
        self, drug_dataset_version: DrugDataSetVersion
    ) -> List[
        DrugData | DrugVal | DrugValRef | DrugCode | DrugValMulti | DrugValMultiRef
    ]:

        log.info("[DRUG DATA IMPORT] Parse drug data...")
        drug_data_objs: Dict[str, DrugData] = {}

        PACKAGE_csv_path = Path(self.source_dir, "PACKAGE.CSV")
        with open(PACKAGE_csv_path, "rt") as package_csc_file:
            package_csv = csv.reader(package_csc_file, delimiter=";")
            package_csv_headers = next(package_csv)
            package_id_column_index = package_csv_headers.index("ID")
            for package_row in package_csv:
                drug_data_obj = DrugData()
                drug_data_objs[package_row[package_id_column_index]] = (
                    await self._parse_drug_data_package_row(
                        drug_dataset_version, package_row, package_csv_headers
                    )
                )

    async def _parse_drug_data_package_row(
        self,
        drug_dataset_version: DrugDataSetVersion,
        package_row: List[str],
        package_row_headers: List[str],
    ) -> DrugData:
        result_drug_data = DrugData(source_dataset=drug_dataset_version)
        for root_prop_name, mapping in root_props_mapping.items():
            drug_prop_value = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=mapping,
            )
            if drug_prop_value == "":
                drug_prop_value = None
            setattr(result_drug_data, root_prop_name, drug_prop_value)
        for drug_code_data in code_attr_definitions:
            drug_code_val = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=drug_code_data.source_mapping,
            )
            result_drug_data.codes.append(
                DrugCode(code_system_id=drug_code_data.field.id, code=drug_code_val)
            )
        for attr_data in attr_definitions:
            drug_code_val = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_data.source_mapping,
            )
            result_drug_data.attrs.append(
                DrugVal(field_name=attr_data.field.field_name, value=drug_code_val)
            )
        for attr_ref_data in attr_ref_definitions:
            drug_code_val = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_data.source_mapping,
            )
            result_drug_data.attrs_ref.append(
                DrugValRef(
                    field_name=attr_ref_data.field.field_name, value=drug_code_val
                )
            )
        for attr_multi_data in attr_multi_definitions:
            drug_attr_values = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_data.source_mapping,
                singular_val=False,
            )
            for index, drug_attr_val in enumerate(drug_attr_values):
                result_drug_data.attrs_multi.append(
                    DrugValMulti(
                        field_name=attr_multi_data.field.field_name,
                        value=drug_attr_val,
                        value_index=index,
                    )
                )
        for attr_multi_data in attr_multi_ref_definitions:
            drug_attr_values = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_data.source_mapping,
                singular_val=False,
            )
            for index, drug_attr_val in enumerate(drug_attr_values):
                result_drug_data.attrs_multi_ref.append(
                    DrugValMultiRef(
                        field_name=attr_multi_data.field.field_name,
                        value=drug_attr_val,
                        value_index=index,
                    )
                )
        return result_drug_data

    async def _resolve_source_mapping_to_value(
        self,
        package_row: List[str],
        package_row_headers: List[str],
        mapping: SourceAttrMapping,
        singular_val: bool = True,
    ) -> List[str] | str:
        if mapping.filename == "PACKAGE.CSV":
            target_col_index = package_row_headers.index(mapping.colname)
            return package_row[target_col_index]
        if mapping.filename != "PACKAGE.CSV" and mapping.source_path is None:
            raise ValueError(
                f"If drug attribute value can not retrieved from PACKAGE.CSV, we need a relative path to the value in the mapping. Mapping: {mapping}"
            )
        return await self._follow_source_mapping_path_to_values(
            current_rows=[package_row],
            row_headers=package_row_headers,
            path=mapping.source_path.split("/"),
            singular_val=singular_val,
        )

    async def _follow_source_mapping_path_to_values(
        self,
        current_rows: List[List[str]],
        row_headers: List[str],
        path: List[str],
        _depth=0,
        singular_val: bool = False,
    ) -> List[str] | str:
        # example for path ["PACKAGE.CSV[PRODUCTID]","ITEM.CSV[PRODUCTID]>[ID]","ITEM_ATC.CSV[ITEMID]"]
        current_path_segment = path[0]
        path_without_current_segment = path[1:]
        is_last_path_segment = len(path) == 1
        is_first_path_segment = _depth == 0
        is_single_segment_path = is_first_path_segment and is_last_path_segment
        result_values = []
        for row in current_rows:
            if is_single_segment_path:
                # sanity check
                raise ValueError(
                    f"We can just extract the value from package.csv. What are you doing here? Path: {path}"
                )
            if is_last_path_segment:
                col_name = extract_bracket_values(current_path_segment, 1)[0]
                col_index = row_headers.index(col_name)
                result_values.extend(row[col_index])
            else:
                # e.g. path[1] -> "ITEM.CSV[PRODUCTID]>[ID]" or "ATC.CSV[PRODUCTID]"
                next_file_name = path[1].split("[")[0]
                next_file_path = Path(self.source_dir, next_file_name)
                if is_first_path_segment:
                    # e.g. "ATC.CSV[PRODUCTID]"
                    next_file_col_name = extract_bracket_values(
                        current_path_segment, 1
                    )[0]
                else:
                    # e.g. "ITEM.CSV[PRODUCTID]>[ID]"
                    next_file_col_name = extract_bracket_values(path[1], 1)[0]

                bridge_col_name = extract_bracket_values(current_path_segment, 1)[0]
                bridge_col_index = row_headers.index(bridge_col_name)
                bridge_col_val = row[bridge_col_index]
                print("next_file_col_name", next_file_col_name)
                next_row_headers, next_rows = (
                    await self._get_rows_with_header_from_csv_file(
                        file_path=next_file_path,
                        id_col_name=next_file_col_name,
                        id_col_val=bridge_col_val,
                        max_number_rows=1 if singular_val else None,
                    )
                )
                result_values.extend(
                    await self._follow_source_mapping_path_to_values(
                        current_rows=next_rows,
                        row_headers=next_row_headers,
                        path=path_without_current_segment,
                        _depth=_depth + 1,
                    )
                )
        if singular_val and len(result_values) > 1:
            # sanity check
            raise ValueError("Singlar value has multiple", path, result_values)
        if singular_val:
            return None if not result_values else result_values[0]
        return result_values

    async def _get_rows_with_header_from_csv_file(
        self,
        id_col_name: str,
        id_col_val: str,
        file_path: Path,
        max_number_rows: int | None = None,
    ) -> Tuple[List[str], List[List[str]]]:
        result = None
        # todo: Some caching of file here could make sense
        result_rows = []
        print("file_path", file_path)
        print("id_col_name", id_col_name)
        print("id_col_val", id_col_val)

        with open(file_path, "rt") as file:
            csvreader = csv.reader(file, delimiter=";")
            headers = next(csvreader)
            id_col_index = headers.index(id_col_name)
            for row in csvreader:
                if row[id_col_index] == id_col_val:
                    result_rows.append(row)
                    if max_number_rows and len(result_rows) == max_number_rows:
                        break
        return headers, result_rows

    async def commit(self, objs):
        """
        num_obj = len(objs)
        for index, obj in enumerate(objs):
            async with get_async_session_context() as session:
                print(index, num_obj)
                session.add(obj)

                await session.commit()
        return
        """
        async with get_async_session_context() as session:
            for obj in objs:
                # log.info(("obj", obj))
                session.add(obj)
            log.info(
                "[DRUG DATA IMPORT] Commit Drug data to database. This may take a while..."
            )
            await session.commit()

    async def _generate_lov_items(
        self,
        paren_field: DrugValRef,
        lov_definition: MmiPiDrugAttrRefFieldLovImportDefinition,
    ) -> List[DrugAttrFieldLovItem]:
        lov_items: List[DrugAttrFieldLovItem] = []
        source_file = Path(self.source_dir, lov_definition.lov_source_file)

        def get_header_index(
            colname: str, headers: List[str], default: Any = Unset
        ) -> int:
            try:
                return headers.index(colname)
            except (IndexError, ValueError) as e:
                if default is not Unset:
                    return default
                raise ValueError(
                    f"[{self.__class__.__name__}] Could not find column '{colname}' in file '{source_file.resolve()}' while parsing LOV/Select/Reference-Values for field '{paren_field.field_name}'. \nExisting headers: {headers}"
                )

        with open(source_file) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            headers: List[str] = next(csvreader)

            for index, row in enumerate(csvreader):

                value = row[get_header_index(lov_definition.values_col_name, headers)]
                display_value = row[
                    get_header_index(lov_definition.display_value_col_name, headers)
                ]
                # filter rows
                if lov_definition.filter_col is not None:
                    filter_col_index = get_header_index(
                        lov_definition.filter_col, headers, default=None
                    )
                    if row[filter_col_index] != lov_definition.filter_val:
                        # we dont want this value in the lov item list
                        # this is primarily used to filter list oif values of MMI's CATALOGENTRY.CSV
                        continue

                li = DrugAttrFieldLovItem(
                    field_name=paren_field.field_name,
                    value=value,
                    display=display_value,
                    sort_order=index,
                )
                lov_items.append(li)

        return lov_items
