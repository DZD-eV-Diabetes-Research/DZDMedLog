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
    Iterator,
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

from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
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
        cast_func=lambda x: bool(int(x)),
    ),
    "attrs.ist_kosmetikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "COSMETICS_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_kosmetikum",
        cast_func=lambda x: bool(int(x)),
    ),
    "attrs.ist_nahrungsergaenzungsmittel": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "DIETARYSUPPLEMENT_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_nahrungsergaenzungsmittel",
        cast_func=lambda x: bool(int(x)),
    ),
    "attrs.ist_pflanzlich": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HERBAL_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_pflanzlich",
        cast_func=lambda x: bool(int(x)),
    ),
    "attrs.ist_generikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "GENERIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_generikum",
        cast_func=lambda x: bool(int(x)),
    ),
    "attrs.ist_homoeopathisch": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HOMOEOPATHIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_homoeopathisch",
        cast_func=lambda x: bool(int(x)),
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


@dataclass
class CsvFileContent:
    headers: List[str]
    rows: List[List[Any]]


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
        self._lov_values: Dict[str, List[DrugAttrFieldLovItem]] = {}
        self._csv_readers_cache: Dict[CsvFileContent]

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

    async def run_import(self):
        # generate schema definitions; fields,lov-defintions,...
        log.info("[DRUG DATA IMPORT] Parse metadata...")
        all_objs = []
        drug_dataset = await self._ensure_drug_dataset_version()
        # generate list of values
        all_attr_defs_by_type = await self.get_all_attr_field_definitions()
        all_attr_defs_flat = []
        for attrdefs in all_attr_defs_by_type.values():
            for attrdef in attrdefs:
                all_attr_defs_flat.append(attrdef)

        all_objs.extend(all_attr_defs_flat)
        for ref_lov_field_obj in attr_ref_definitions + attr_multi_ref_definitions:
            all_objs.append(ref_lov_field_obj.field)
            lov_item_objs = await self._generate_lov_items(
                ref_lov_field_obj.field, lov_definition=ref_lov_field_obj.lov
            )
            self._lov_values[ref_lov_field_obj.field.field_name] = lov_item_objs

            all_objs.extend(lov_item_objs)

        # read all drugs with attributes
        drug_data_objs: Dict[str, DrugData] = await self._parse_drug_data(drug_dataset)
        log.info(("ALL", drug_data_objs))

        all_objs.extend(drug_data_objs.values())

        # write everything to database
        await self.commit(all_objs)

    async def _parse_drug_data(
        self, drug_dataset_version: DrugDataSetVersion
    ) -> List[
        DrugData | DrugVal | DrugValRef | DrugCode | DrugValMulti | DrugValMultiRef
    ]:

        log.info("[DRUG DATA IMPORT] Parse drug data...")
        package_csv_path = Path(self.source_dir, "PACKAGE.CSV")

        row_count = 0
        # count rows
        with open(package_csv_path) as f:
            row_count = len(f.readlines()) - 1
        # parse csv
        drug_data_objs: Dict[str, DrugData] = {}
        with open(package_csv_path, "rt") as package_csv_file:
            package_csv = csv.reader(package_csv_file, delimiter=";")
            package_csv_headers = next(package_csv)
            package_id_column_index = package_csv_headers.index("ID")
            for index, package_row in enumerate(package_csv):
                if index % 100 == 0:
                    log.info(
                        f"[DRUG DATA IMPORT] Processed {index} rows from {row_count}"
                    )
                drug_data_objs[package_row[package_id_column_index]] = (
                    await self._parse_drug_data_package_row(
                        drug_dataset_version, package_row, package_csv_headers
                    )
                )
        # print("drug_data_objs", drug_data_objs)
        return drug_data_objs

    async def _parse_drug_data_package_row(
        self,
        drug_dataset_version: DrugDataSetVersion,
        package_row: List[str],
        package_row_headers: List[str],
    ) -> DrugData:
        result_drug_data = DrugData(source_dataset=drug_dataset_version)
        # drug root attrs
        for root_prop_name, mapping in root_props_mapping.items():
            drug_attr_value = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=mapping,
            )
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, mapping
            )
            setattr(result_drug_data, root_prop_name, drug_attr_value)
        # drug codes
        for drug_code_data in code_attr_definitions:
            drug_code_value = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=drug_code_data.source_mapping,
            )
            drug_code_value = self._cast_raw_csv_value_if_needed(
                drug_code_value, drug_code_data.source_mapping
            )
            if drug_code_value is None:
                continue
            # await self._validate_csv_value(
            #    value=drug_code_value, mapping=drug_code_data.source_mapping
            # )
            result_drug_data.codes.append(
                DrugCode(code_system_id=drug_code_data.field.id, code=drug_code_value)
            )
        # drug attrs
        for attr_data in attr_definitions:
            drug_attr_value = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_data.source_mapping,
            )
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, attr_data.source_mapping
            )
            await self._validate_csv_value(
                value=drug_attr_value, mapping=attr_data.source_mapping
            )
            result_drug_data.attrs.append(
                DrugVal(field_name=attr_data.field.field_name, value=drug_attr_value)
            )
        # drug ref attr
        for attr_ref_data in attr_ref_definitions:
            drug_attr_value = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_ref_data.source_mapping,
            )
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, attr_ref_data.source_mapping
            )
            await self._validate_csv_value(
                value=drug_attr_value, mapping=attr_ref_data.source_mapping
            )

            result_drug_data.attrs_ref.append(
                DrugValRef(
                    field_name=attr_ref_data.field.field_name, value=drug_attr_value
                )
            )
        # drug multi attrs
        for attr_multi_data in attr_multi_definitions:
            drug_attr_values = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_multi_data.source_mapping,
                singular_val=False,
            )
            for index, drug_attr_val in enumerate(drug_attr_values):
                drug_attr_val = self._cast_raw_csv_value_if_needed(
                    drug_attr_val, attr_multi_data.source_mapping
                )
                await self._validate_csv_value(
                    value=drug_attr_value, mapping=attr_multi_data.source_mapping
                )
                result_drug_data.attrs_multi.append(
                    DrugValMulti(
                        field_name=attr_multi_data.field.field_name,
                        value=drug_attr_val,
                        value_index=index,
                    )
                )
        # drug multi ref attrs
        for attr_multi_ref_data in attr_multi_ref_definitions:
            drug_attr_values = await self._resolve_source_mapping_to_value(
                package_row=package_row,
                package_row_headers=package_row_headers,
                mapping=attr_multi_ref_data.source_mapping,
                singular_val=False,
            )
            # log.debug(("drug_attr_values",drug_attr_values))
            # log.debug(("package_row",package_row))
            for index, drug_attr_val in enumerate(drug_attr_values):
                # log.debug(("BEFORE: drug_attr_val",drug_attr_val))
                drug_attr_val = self._cast_raw_csv_value_if_needed(
                    drug_attr_val, attr_multi_ref_data.source_mapping
                )
                # log.debug(("AFTER: drug_attr_val",drug_attr_val))

                await self._validate_csv_value(
                    value=drug_attr_val, mapping=attr_multi_ref_data.source_mapping
                )
                result_drug_data.attrs_multi_ref.append(
                    DrugValMultiRef(
                        field_name=attr_multi_ref_data.field.field_name,
                        value=drug_attr_val,
                        value_index=index,
                    )
                )
        return result_drug_data

    def _cast_raw_csv_value_if_needed(self, value: Any, mapping: SourceAttrMapping):
        if value == "" or value is None:
            return None
        if mapping.cast_func:
            return mapping.cast_func(value)
        return value

    async def _validate_csv_value(self, value: str, mapping: SourceAttrMapping):
        all_defs = await self.get_all_attr_field_definitions()
        mapping_attr = mapping.map2.split(".")
        if len(mapping_attr) == 1:
            # todo: valdiate root values
            return
        attr_type, attr_name = mapping_attr

        target_attr_def: DrugAttrFieldDefinition = next(
            (d for d in all_defs[attr_type] if d.field_name == attr_name), None
        )
        if target_attr_def is None:
            raise ValueError(
                f"No attribute defintion  with name '{attr_name}' existent."
            )
        """
        if target_attr_def.is_multi_val_field and not isinstance(value,list):
            raise ValueError(f"Expected '{mapping_attr}' to be a list. Got {value}")
        if target_attr_def.is_multi_val_field and isinstance(value,list):
            raise ValueError(f"Expected '{mapping_attr}' to be a single value. Got {value}")
        """
        if value is None and target_attr_def.optional == True:
            # all fine
            return
        if target_attr_def.is_reference_list_field:
            ref_value_exists = False
            for lov_item in self._lov_values[attr_name]:
                if lov_item.value == value:
                    ref_value_exists = True
                    break
            if not ref_value_exists:
                raise ValueError(
                    f"Reference object for {mapping_attr} does not exists for value '{value}'. Possible values: \n{self._lov_values[attr_name]}"
                )
        try:
            target_attr_def.type.value.casting_func(value)
        except:
            raise ValueError(
                f"Could not cast raw value '{value}' to type {target_attr_def.type.value.python_type} as defined in {target_attr_def}"
            )

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
        return await self._follow_source_mapping_path_to_target_vals(
            target_col_name=mapping.colname,
            current_rows=[package_row],
            row_headers=package_row_headers,
            path=mapping.source_path.split("/"),
            singular_val=singular_val,
        )

    async def _follow_source_mapping_path_to_target_vals(
        self,
        target_col_name: str,
        current_rows: List[List[str]],
        row_headers: List[str],
        path: List[str],
        singular_val: bool = False,
        _depth=0,
    ) -> List[str]:
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
                col_index = row_headers.index(target_col_name)
                result_values.append(row[col_index])
            else:
                next_file_name = path[1].split("[")[0]
                next_file_path = Path(self.source_dir, next_file_name)
                if is_first_path_segment:
                    # e.g. "ITEM.CSV[PRODUCTID]>[ID]"
                    next_file_col_name = extract_bracket_values(path[1], 1)[0]
                    bridge_col_name = extract_bracket_values(current_path_segment, 1)[0]
                    bridge_col_index = row_headers.index(bridge_col_name)
                    bridge_col_val = row[bridge_col_index]
                    next_row_headers, next_rows = (
                        await self._get_rows_with_header_from_csv_file(
                            file_path=next_file_path,
                            id_col_name=next_file_col_name,
                            id_col_val=bridge_col_val,
                            max_number_rows=1 if singular_val else None,
                        )
                    )
                else:
                    # e.g. path[1] -> "ITEM.CSV[PRODUCTID]>[ID]" or "ATC.CSV[PRODUCTID]"
                    # "PACKAGE.CSV[PRODUCTID]/ITEM.CSV[PRODUCTID]>[ID]/ITEM_ATC.CSV[ITEMID]"
                    next_file_col_name = extract_bracket_values(path[1], 1)[0]
                    bridge_col_name = extract_bracket_values(current_path_segment, 1)[0]
                    bridge_col_index = row_headers.index(bridge_col_name)
                    bridge_col_val = row[bridge_col_index]
                    next_row_headers, next_rows = (
                        await self._get_rows_with_header_from_csv_file(
                            file_path=next_file_path,
                            id_col_name=next_file_col_name,
                            id_col_val=bridge_col_val,
                            max_number_rows=1 if singular_val else None,
                        )
                    )
                result_values.extend(
                    await self._follow_source_mapping_path_to_target_vals(
                        target_col_name=target_col_name,
                        current_rows=next_rows,
                        row_headers=next_row_headers,
                        path=path_without_current_segment,
                        _depth=_depth + 1,
                    )
                )
        if singular_val and len(result_values) > 1:
            # sanity check
            raise ValueError(
                "Singlar value has multiple",
                "PATH:",
                path,
                "VALUES:",
                result_values,
                "ROWS",
                current_rows,
            )
        if singular_val:
            return None if not result_values else result_values[0]
        return result_values

    async def _get_csv_file_rows_with_header(self, file_path: Path) -> CsvFileContent:
        if file_path not in self._csv_readers_cache:
            with open(file_path, "rt") as file:
                csvreader = csv.reader(file, delimiter=";")
                headers = next(csvreader)
                self._csv_readers_cache[file_path] = CsvFileContent(
                    headers=headers, rows=list(csvreader)
                )
        return self._csv_readers_cache[file_path]

    async def _get_rows_with_header_from_csv_file(
        self,
        id_col_name: str,
        id_col_val: str,
        file_path: Path,
        max_number_rows: int | None = None,
    ) -> Tuple[List[str], List[List[str]]]:
        # todo: Some caching of file here could make sense
        result_rows = []
        with open(file_path, "rt") as file:
            csvreader = csv.reader(file, delimiter=";")
            headers = next(csvreader)
            try:
                id_col_index = headers.index(id_col_name)
            except ValueError:
                raise ValueError(
                    f"Can not find '{id_col_name}' in headers of file {file_path.absolute()}. headers: {headers}"
                )
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
                try:
                    session.add(obj)
                except:
                    log.error(("Failed obj", obj))
                    raise
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
