from typing import (
    List,
    Callable,
    Dict,
    Optional,
    Any,
    Literal,
    Type,
    Union,
    AsyncGenerator,
    Self,
)
import uuid
import time
from pathlib import Path
import datetime
import csv
from dataclasses import dataclass, field
from sqlmodel import SQLModel, select, and_
from medlogserver.db._session import (
    get_async_session_context,
    AsyncSession,
)
from sqlalchemy import insert, text
import polars as pl
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValRef,
    DrugValMulti,
    DrugValMultiRef,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    ValueTypeCasting,
    DisplayPriorityClass,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import (
    DrugAttrFieldLovItem,
)
from medlogserver.db.drug_data.importers._base import (
    DrugDataSetImporterBase,
    DrugDataSetImporterCapabilities,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug import DrugData
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.log import get_logger
from medlogserver.config import Config
from medlogserver.model.unset import Unset
from medlogserver.utils import (
    async_enumerate,
    FTPClient,
    is_version_higher,
    highest_version,
    unzip,
)
import gc


config = Config()
log = get_logger(modulename="DRUGIMPORT")
importername = "MMIPharmindex1_32"


@dataclass
class MmiPiDrugAttrRefFieldLovImportDefinition:
    lov_source_file: Optional[str] = "CATALOGENTRY.CSV"
    additional_lov_source_files: List[str] = field(default_factory=list)
    values_col_name: Optional[str] = "CODE"
    display_value_col_name: Optional[str] = "NAME"
    filter_col: Optional[str] = "CATALOGID"
    filter_val: Optional[str] = None
    sort_attr: Optional[Literal["field_name", "value", "display"]] = None
    display_name_factory: Optional[Callable[[str, str, str], str]] = (
        lambda field_name, value, display: display
    )


@dataclass
class SourceAttrMapping:
    filename: str
    colname: str
    source_path: Optional[str] = (
        None  # documents the join path from PACKAGE.CSV to the source column
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
        map2="trade_name",
    ),
    "market_access_date": SourceAttrMapping(
        "PACKAGE.CSV",
        "ONMARKETDATE",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").date(),
    ),
    "market_exit_date": SourceAttrMapping(
        "ARCHIVE_PACKAGE.CSV",
        "OFFMARKETDATE",
        map2="market_exit_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").date(),
    ),
    # codes
    "codes.PZN": SourceAttrMapping(
        "PACKAGE.CSV",
        "PZN",
        map2="codes.PZN",
    ),
    "codes.MMIP": SourceAttrMapping(
        "PACKAGE.CSV",
        "PRODUCTID",
        map2="codes.MMIP",
    ),
    "attrs_multi.ATC": SourceAttrMapping(
        "ITEM_ATC.CSV",
        "ATCCODE",
        source_path="PACKAGE.CSV[PRODUCTID]/ITEM.CSV[PRODUCTID]>[ID]/ITEM_ATC.CSV[ITEMID]",
        map2="attrs_multi.ATC",
    ),
    # attrs
    "attrs.amount": SourceAttrMapping(
        "PACKAGE.CSV",
        "AMOUNTTEXT",
        map2="attrs.amount",
    ),
    "attrs.ist_verhuetungsmittel": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "CONTRACEPTIVE_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_verhuetungsmittel",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    "attrs.ist_kosmetikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "COSMETICS_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_kosmetikum",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    "attrs.ist_nahrungsergaenzungsmittel": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "DIETARYSUPPLEMENT_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_nahrungsergaenzungsmittel",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    "attrs.ist_pflanzlich": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HERBAL_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_pflanzlich",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    "attrs.ist_generikum": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "GENERIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_generikum",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    "attrs.ist_homoeopathisch": SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HOMOEOPATHIC_FLAG",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_FLAG.CSV[PRODUCTID]",
        map2="attrs.ist_homoeopathisch",
        cast_func=lambda x: bool(int(x)) if x is not None else None,
    ),
    # ref attrs
    "attrs_ref.darreichungsform": SourceAttrMapping(
        "PACKAGE.CSV",
        "IFAPHARMFORMCODE",
        map2="attrs_ref.darreichungsform",
    ),
    "attrs_ref.vertriebsstatus": SourceAttrMapping(
        "PACKAGE.CSV",
        "SALESSTATUSCODE",
        map2="attrs_ref.vertriebsstatus",
    ),
    "attrs_ref.normgroesse": SourceAttrMapping(
        "PACKAGE.CSV",
        "PACKAGENORMSIZECODE",
        map2="attrs_ref.normgroesse",
    ),
    "attrs_ref.abgabestatus": SourceAttrMapping(
        "PRODUCT.CSV",
        "DISPENSINGTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.abgabestatus",
    ),
    "attrs_ref.lebensmittel": SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTFOODTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.lebensmittel",
    ),
    "attrs_ref.diaetetikum": SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTDIETETICSTYPECODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT.CSV[ID]",
        map2="attrs_ref.diaetetikum",
    ),
    "attrs_ref.hersteller": SourceAttrMapping(
        "PRODUCT_COMPANY.CSV",
        "COMPANYID",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_COMPANY.CSV[PRODUCTID]",
        map2="attrs_ref.hersteller",
        filter_colname="PRODUCTCOMPANYTYPECODE",
        filter_colval="M",
    ),
    # multi ref attrs
    "attrs_multi_ref.applikationsart": SourceAttrMapping(
        "ITEM.CSV",
        "ITEMROACODE",
        source_path="PACKAGE.CSV[PRODUCTID]/ITEM.CSV[PRODUCTID]",
        map2="attrs_multi_ref.applikationsart",
    ),
    "attrs_multi_ref.keywords": SourceAttrMapping(
        "PRODUCT_KEYWORD.CSV",
        "CODE",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_KEYWORD.CSV[PRODUCTID]",
        map2="attrs_multi_ref.keywords",
    ),
    "attrs_multi_ref.icd10": SourceAttrMapping(
        "PRODUCT_ICD.CSV",
        "ICDCODE",
        map2="attrs_multi_ref.icd10",
        source_path="PACKAGE.CSV[PRODUCTID]/PRODUCT_ICD.CSV[PRODUCTID]",
    ),
}

root_props_mapping = {
    prop_name: mapping
    for prop_name, mapping in mmi_rohdaten_r3_mappings.items()
    if not "." in prop_name
}


def get_code_attr_definitions() -> List[DrugAttrFieldDefinitionContainer]:
    return [
        DrugAttrFieldDefinitionContainer(
            field=DrugCodeSystem(
                id="PZN",
                name="Pharmazentralnummer",
                country="Germany",
                optional=False,
                unique=True,
                importer_name=importername,
                code_display_sort_order=1,
                client_visible=True,
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
                importer_name=importername,
                code_display_sort_order=2,
                client_visible=False,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["codes.MMIP"],
        ),
    ]


def get_attr_definitions() -> List[DrugAttrFieldDefinitionContainer]:
    return [
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="amount",
                field_name_display="Menge",
                field_desc="Menge in der Produktpackung",
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=["3.5 g", "2x100 ml", "60 st"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=1,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.amount"],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_verhuetungsmittel",
                field_name_display="Verhütungsmittel",
                field_desc="Ist das Produkt ein Verhütungsmittel",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[True, False],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=1,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_verhuetungsmittel"],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_kosmetikum",
                field_name_display="Kosmetikum",
                field_desc="Ist das Produkt ein Kosmetikum",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[True, False],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=10,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_kosmetikum"],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_nahrungsergaenzungsmittel",
                field_name_display="Nahrungsergänzungsmittel",
                field_desc="Ist das Produkt ein Nahrungsergänzungsmittel",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[True, False],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=2,
            ),
            source_mapping=mmi_rohdaten_r3_mappings[
                "attrs.ist_nahrungsergaenzungsmittel"
            ],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_pflanzlich",
                field_name_display="Pflanzlich",
                field_desc="Ist das Produkt Pflanzlich",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[True, False],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=3,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_pflanzlich"],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_generikum",
                field_name_display="Generikum",
                field_desc="Ist das Produkt ein Generikum",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[1, 0],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=3,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_generikum"],
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ist_homoeopathisch",
                field_name_display="Homöopathisch",
                field_desc="Ist das Produkt Homöopathisch",
                value_type=ValueTypeCasting.BOOL,
                optional=True,
                default=None,
                is_reference_list_field=False,
                is_multi_val_field=False,
                examples=[1, 0],
                importer_name=importername,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=4,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs.ist_homoeopathisch"],
        ),
    ]


def get_attr_multi_definitions() -> List[DrugAttrFieldDefinitionContainer]:
    return [
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="ATC",
                field_name_display="ATC Codes",
                field_desc="Anatomical Therapeutic Chemical code. A unique code assigned to a medicine according to the organ or system it works on and how it works. The classification system is maintained by the World Health Organization (WHO). ",
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=False,
                is_multi_val_field=True,
                examples=["D04AA04", "V60A"],
                importer_name=importername,
                searchable=True,
                field_display_priority_class=DisplayPriorityClass.CLASS1,
                field_display_sort_order=1,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs_multi.ATC"],
        )
    ]


def get_attr_ref_definitions() -> List[DrugAttrFieldDefinitionContainer]:
    return [
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="darreichungsform",
                field_name_display="Darreichungsform",
                field_desc="Darreichungsform IFA",
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["AUGEN", "DIL"],
                importer_name=importername,
                searchable=True,
                field_display_priority_class=DisplayPriorityClass.CLASS1,
                field_icon=None,
                field_display_sort_order=5,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.darreichungsform"],
            lov=MmiPiDrugAttrRefFieldLovImportDefinition(
                filter_val="109", sort_attr="display"
            ),
        ),
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="vertriebsstatus",
                field_name_display="Vertriebsstatus",
                field_desc="Wird das Produkt momentan vertrieben",
                value_type=ValueTypeCasting.STR,
                optional=False,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["D", "F"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS1,
                field_icon=None,
                field_display_sort_order=2,
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
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["A", "1"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=4,
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
                value_type=ValueTypeCasting.INT,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["0", "2"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=5,
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
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["E", "N", "Y"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=8,
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
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=False,
                examples=["E", "N", "Y"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=4,
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
                value_type=ValueTypeCasting.STR,
                optional=False,
                is_reference_list_field=True,
                is_multi_val_field=False,
                is_large_reference_list=True,
                examples=["13819", "15777", "12"],
                importer_name=importername,
                searchable=False,
                field_display_priority_class=DisplayPriorityClass.CLASS1,
                field_icon=None,
                field_display_sort_order=0,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs_ref.hersteller"],
            lov=MmiPiDrugAttrRefFieldLovImportDefinition(
                lov_source_file="COMPANY.CSV",
                additional_lov_source_files=["ARCHIVE_COMPANY.CSV"],
                values_col_name="ID",
                display_value_col_name="NAME",
                filter_col=None,
                filter_val=None,
            ),
        ),
    ]


def get_attr_multi_ref_definitions() -> List[DrugAttrFieldDefinitionContainer]:
    return [
        DrugAttrFieldDefinitionContainer(
            field=DrugAttrFieldDefinition(
                field_name="applikationsart",
                field_name_display="Applikationsart",
                field_desc="Art und Weise wie ein Arzneimittel verabreicht wird",
                value_type=ValueTypeCasting.INT,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=True,
                examples=["104", "19"],
                importer_name=importername,
                searchable=True,
                field_display_priority_class=DisplayPriorityClass.CLASS1,
                field_icon=None,
                field_display_sort_order=6,
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
                value_type=ValueTypeCasting.INT,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=True,
                examples=["8", "23", "70"],
                importer_name=importername,
                searchable=True,
                field_display_priority_class=DisplayPriorityClass.CLASS3,
                field_icon=None,
                field_display_sort_order=9,
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
                value_type=ValueTypeCasting.STR,
                optional=True,
                is_reference_list_field=True,
                is_multi_val_field=True,
                examples=["A01.0, M01.39", "B44.8 K23.8", "F41.1"],
                importer_name=importername,
                searchable=True,
                field_display_priority_class=DisplayPriorityClass.CLASS2,
                field_icon=None,
                field_display_sort_order=9,
            ),
            source_mapping=mmi_rohdaten_r3_mappings["attrs_multi_ref.icd10"],
            lov=MmiPiDrugAttrRefFieldLovImportDefinition(
                filter_val="18",
                display_name_factory=lambda field_name, value, display: (
                    f"{value} - {display}"
                ),
            ),
        ),
    ]


class MMIPharmindex1_32(DrugDataSetImporterBase):
    def __init__(self):
        self.dataset_name = "MMI Pharmindex"
        self.api_name = importername
        self.dataset_link = "https://www.MmiPi.de/forschung-projekte/arzneimittel/gkv-arzneimittelindex/"
        self.source_dir = None
        self.version = None
        self.capabilities: DrugDataSetImporterCapabilities = (
            DrugDataSetImporterCapabilities(
                can_check_for_remote_updates=True,
                can_be_triggered_for_manual_update=True,
                can_download_remote_updates=True,
            )
        )
        self._ensured_dataset_version: DrugDataSetVersion = None
        self.batch_size = config.DRUG_IMPORTER_BATCH_SIZE
        self._attr_def_cache = {}
        self._db_session: AsyncSession | None = None

    def _get_ftp_client_for_remote_drug_data_source(self) -> FTPClient | None:
        ftp_client: FTPClient | None = None
        if config.DRUG_IMPORTER_SOURCE_FTP_HOST:
            log.debug(
                f"Connect to FTP `{config.DRUG_IMPORTER_SOURCE_FTP_HOST}:{config.DRUG_IMPORTER_SOURCE_FTP_PORT}` with `{config.DRUG_IMPORTER_SOURCE_FTP_USER}/{config.DRUG_IMPORTER_SOURCE_FTP_PASSWORD}`"
            )
            ftp_client = FTPClient(
                host=config.DRUG_IMPORTER_SOURCE_FTP_HOST,
                user=config.DRUG_IMPORTER_SOURCE_FTP_USER,
                port=config.DRUG_IMPORTER_SOURCE_FTP_PORT,
                password=config.DRUG_IMPORTER_SOURCE_FTP_PASSWORD,
            )
            log.debug(
                f"Check FTP `{config.DRUG_IMPORTER_SOURCE_FTP_HOST}:{config.DRUG_IMPORTER_SOURCE_FTP_PORT}` is available."
            )
            ftp_client.is_server_up(timeout=1)
            log.debug(
                f"FTP `{config.DRUG_IMPORTER_SOURCE_FTP_HOST}:{config.DRUG_IMPORTER_SOURCE_FTP_PORT}` seems healthy."
            )
            return ftp_client

    async def check_for_remote_latest_dataset_version(self) -> str | None:
        ftp_client = self._get_ftp_client_for_remote_drug_data_source()
        if ftp_client is None:
            return None

        remote_file_list = ftp_client.list_files(remote_dir="MMI_RohdatenR3")
        remote_versions = [
            d.name.rstrip(".zip") for d in remote_file_list if d.type_ == "file"
        ]
        if not remote_versions:
            return None
        return highest_version(remote_versions)

    async def download_remote_dataset_update(self) -> Self | None:
        """Download a newer remote drug dataset if one is available."""
        new_version_string = await self.check_for_remote_dataset_update_available()
        if not new_version_string:
            return None

        ftp_client = self._get_ftp_client_for_remote_drug_data_source()
        if not ftp_client:
            return None
        Path(config.DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR).mkdir(
            parents=True, exist_ok=True
        )

        target_unzip_dir_path = Path(
            config.DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR,
            f"{new_version_string}",
        )
        new_remote_version_zip_file = None
        for remote_obj in ftp_client.list_files(remote_dir="MMI_RohdatenR3"):
            if remote_obj.type_ == "dir":
                continue
            elif remote_obj.name.endswith(".zip"):
                new_remote_version_zip_file = remote_obj.name
        if new_remote_version_zip_file is None:
            return None
        target_download_path = Path(
            config.DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR,
            f"{new_remote_version_zip_file}.zip",
        )
        remote_path = Path("MMI_RohdatenR3", new_remote_version_zip_file)
        log.info(f"Download drug data update `{remote_path} from `{ftp_client.host}`")
        ftp_client.download_file(
            remote_path=remote_path,
            local_path=target_download_path,
        )
        target_unzip_dir_path.mkdir(exist_ok=True)
        dummy_dataset_dir = unzip(
            zip_path=target_download_path,
            destination=target_unzip_dir_path,
            unwrap_single_dir=True,
        )

        self.source_dir = dummy_dataset_dir
        self.version = new_version_string
        return self

    async def get_already_imported_datasets(
        self,
    ) -> List[DrugDataSetVersion]:
        print("DummyDrugs", self.dataset_name)
        all_rows = []
        async with get_async_session_context() as session:
            query = (
                select(DrugDataSetVersion)
                .where(
                    and_(
                        DrugDataSetVersion.dataset_source_name == self.dataset_name,
                        DrugDataSetVersion.is_custom_drugs_collection == False,
                    )
                )
                .order_by(DrugDataSetVersion.dataset_version)
            )
            result = await session.exec(query)
            all_rows = result.all()
        return list(all_rows)

    async def was_dataset_version_imported(self) -> DrugDataSetVersion | None:
        imported_datasets = await self.get_already_imported_datasets()
        for imported_dataset in imported_datasets:
            if (
                imported_dataset.dataset_version == self.version
                and imported_dataset.import_status in ["running", "done"]
            ):
                return imported_dataset
        return None

    async def get_drug_dataset_version(self) -> str:
        if self.version is None and self.source_dir is not None:
            source_dir_name = Path(self.source_dir).name
            self.version = source_dir_name
        return self.version

    async def get_attr_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if "attr_definitions" not in self._attr_def_cache:
            self._attr_def_cache["attr_definitions"] = get_attr_definitions()
        if by_name:
            return [
                attr_def.field
                for attr_def in self._attr_def_cache["attr_definitions"]
                if attr_def.field.field_name == by_name
            ]
        return [attr_def.field for attr_def in self._attr_def_cache["attr_definitions"]]

    async def get_attr_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if "attr_ref_definitions" not in self._attr_def_cache:
            self._attr_def_cache["attr_ref_definitions"] = get_attr_ref_definitions()
        if by_name:
            return [
                attr_def.field
                for attr_def in self._attr_def_cache["attr_ref_definitions"]
                if attr_def.field.field_name == by_name
            ]
        return [
            field_def.field
            for field_def in self._attr_def_cache["attr_ref_definitions"]
        ]

    async def get_attr_multi_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if "attr_multi_definitions" not in self._attr_def_cache:
            self._attr_def_cache["attr_multi_definitions"] = (
                get_attr_multi_definitions()
            )
        if by_name:
            return [
                attr_def.field
                for attr_def in self._attr_def_cache["attr_multi_definitions"]
                if attr_def.field.field_name == by_name
            ]
        return [
            field_def.field
            for field_def in self._attr_def_cache["attr_multi_definitions"]
        ]

    async def get_attr_multi_ref_field_definitions(
        self, by_name: Optional[str] = None
    ) -> List[DrugAttrFieldDefinition]:
        if "attr_multi_ref_definitions" not in self._attr_def_cache:
            self._attr_def_cache["attr_multi_ref_definitions"] = (
                get_attr_multi_ref_definitions()
            )
        if by_name:
            return [
                field_def.field
                for field_def in self._attr_def_cache["attr_multi_ref_definitions"]
                if field_def.field.field_name == by_name
            ]
        return [
            field_def.field
            for field_def in self._attr_def_cache["attr_multi_ref_definitions"]
        ]

    async def get_code_definitions(
        self, by_id: Optional[str] = None
    ) -> List[DrugCodeSystem]:
        if "code_attr_definitions" not in self._attr_def_cache:
            self._attr_def_cache["code_attr_definitions"] = get_code_attr_definitions()
        if by_id:
            return [
                field_def.field
                for field_def in self._attr_def_cache["code_attr_definitions"]
                if field_def.field.field_name == by_id
            ]
        return [
            field_def.field
            for field_def in self._attr_def_cache["code_attr_definitions"]
        ]

    async def run_import(self):
        async with get_async_session_context() as db_session:
            self._db_session = db_session
            is_sqlite = config.SQL_DATABASE_URL.startswith("sqlite")
            is_pg = config.SQL_DATABASE_URL.startswith("postgresql")
            try:
                if is_sqlite:
                    # Reduce fsync overhead during bulk import.
                    # synchronous=OFF is safe here because a failed import is re-runnable
                    # and leaves behind a dataset version marked "failed".
                    for pragma in [
                        "PRAGMA journal_mode=WAL",
                        "PRAGMA synchronous=OFF",
                        "PRAGMA cache_size=-65536",
                        "PRAGMA temp_store=MEMORY",
                    ]:
                        await db_session.exec(text(pragma))
                    await db_session.commit()
                elif is_pg:
                    # WAL fsync on commit is the dominant latency for small batches.
                    # OFF is safe: a crashed import leaves a "failed" dataset version
                    # that can be re-imported; we never lose already-committed prior data.
                    await db_session.execute(text("SET synchronous_commit = OFF"))

                log.info(" Parse metadata...")
                drug_dataset = await self._ensure_drug_dataset_version()

                drug_schema_objects = []
                for ref_lov_field_obj in (
                    get_attr_ref_definitions() + get_attr_multi_ref_definitions()
                ):
                    lov_item_objs = await self._generate_lov_items(
                        ref_lov_field_obj.field,
                        lov_definition=ref_lov_field_obj.lov,
                        drug_dataset_version=drug_dataset,
                    )
                    drug_schema_objects.extend(lov_item_objs)

                await self.add_and_flush(objs=drug_schema_objects)
                del drug_schema_objects
                self._attr_def_cache.clear()
                gc.collect()

                drug_data_objs: dict[type, List[dict]] = {}
                async for i, drug_obj in async_enumerate(
                    self._parse_drug_data(drug_dataset)
                ):
                    for table_type, data in drug_obj.items():
                        if table_type not in drug_data_objs:
                            drug_data_objs[table_type] = []
                        drug_data_objs[table_type].extend(data)
                    if i > 0 and i % self.batch_size == 0:
                        await self.add_and_flush(table_data=drug_data_objs)

                if drug_data_objs:
                    await self.add_and_flush(table_data=drug_data_objs)

                # safety-net commit for any pending ORM state (e.g. if no drug rows)
                await self.commit()

            finally:
                try:
                    if is_sqlite:
                        await db_session.exec(text("PRAGMA synchronous=FULL"))
                        await db_session.exec(text("PRAGMA cache_size=-2000"))
                        await db_session.commit()
                    elif is_pg:
                        await db_session.execute(text("SET synchronous_commit = ON"))
                        await db_session.commit()
                except Exception as cleanup_err:
                    log.warning(
                        f"Failed to reset session settings after import (session may be in a broken state): {cleanup_err}"
                    )

    def _build_joined_dataframe(self) -> pl.DataFrame:
        """Load all required CSV files and join them into one wide DataFrame.

        Resolves all cross-file attribute paths (documented in source_path fields
        of mmi_rohdaten_r3_mappings) upfront with polars joins. The result is a
        single DataFrame where each row is one PACKAGE with all its attributes
        as flat columns (scalar) or list columns (multi-value).
        """
        src = self.source_dir
        log.info(" Loading and joining CSV source files...")

        package_df = pl.read_csv(
            Path(src, "PACKAGE.CSV"),
            separator=";",
            infer_schema_length=0,
        )

        product_cols = pl.read_csv(
            Path(src, "PRODUCT.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(
            [
                "ID",
                "DISPENSINGTYPECODE",
                "PRODUCTFOODTYPECODE",
                "PRODUCTDIETETICSTYPECODE",
            ]
        )

        product_flag_cols = pl.read_csv(
            Path(src, "PRODUCT_FLAG.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(
            [
                "PRODUCTID",
                "CONTRACEPTIVE_FLAG",
                "COSMETICS_FLAG",
                "DIETARYSUPPLEMENT_FLAG",
                "HERBAL_FLAG",
                "GENERIC_FLAG",
                "HOMOEOPATHIC_FLAG",
            ]
        )

        # One manufacturer per product — keep the first M-type company entry
        manufacturer_cols = (
            pl.read_csv(
                Path(src, "PRODUCT_COMPANY.CSV"),
                separator=";",
                infer_schema_length=0,
            )
            .filter(pl.col("PRODUCTCOMPANYTYPECODE") == "M")
            .select(["PRODUCTID", "COMPANYID"])
            .unique("PRODUCTID")
        )

        item_df = pl.read_csv(
            Path(src, "ITEM.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(["ID", "PRODUCTID", "ITEMROACODE"])

        item_atc_df = pl.read_csv(
            Path(src, "ITEM_ATC.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(["ITEMID", "ATCCODE"])

        # Resolve PACKAGE→ITEM→ITEM_ATC; collect ATC codes as list per PRODUCTID
        atc_per_product = (
            item_df.select(["ID", "PRODUCTID"])
            .join(item_atc_df, left_on="ID", right_on="ITEMID", how="left")
            .group_by("PRODUCTID")
            .agg(pl.col("ATCCODE").drop_nulls().unique())
        )

        # One product can have multiple items with different routes of administration
        roa_per_product = (
            item_df.select(["PRODUCTID", "ITEMROACODE"])
            .filter(pl.col("ITEMROACODE").is_not_null() & (pl.col("ITEMROACODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("ITEMROACODE").unique())
        )

        keywords_per_product = (
            pl.read_csv(
                Path(src, "PRODUCT_KEYWORD.CSV"),
                separator=";",
                infer_schema_length=0,
            )
            .select(["PRODUCTID", "CODE"])
            .filter(pl.col("CODE").is_not_null() & (pl.col("CODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("CODE").unique())
        )

        icd_per_product = (
            pl.read_csv(
                Path(src, "PRODUCT_ICD.CSV"),
                separator=";",
                infer_schema_length=0,
            )
            .select(["PRODUCTID", "ICDCODE"])
            .filter(pl.col("ICDCODE").is_not_null() & (pl.col("ICDCODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("ICDCODE").unique())
        )

        return (
            package_df.join(
                product_cols, left_on="PRODUCTID", right_on="ID", how="left"
            )
            .join(product_flag_cols, on="PRODUCTID", how="left")
            .join(manufacturer_cols, on="PRODUCTID", how="left")
            .join(atc_per_product, on="PRODUCTID", how="left")
            .join(roa_per_product, on="PRODUCTID", how="left")
            .join(keywords_per_product, on="PRODUCTID", how="left")
            .join(icd_per_product, on="PRODUCTID", how="left")
            .with_columns(pl.lit(None).alias("OFFMARKETDATE"))
        )

    def _build_archive_joined_dataframe(self) -> pl.DataFrame:
        """Load ARCHIVE_* CSVs and join supporting tables into the same wide shape
        as _build_joined_dataframe so both can be concatenated and processed by the
        same _parse_drug_data_row logic.

        Archive packages have OFFMARKETDATE set. Columns absent from the archive
        schema (AMOUNTTEXT, IFAPHARMFORMCODE, etc.) are left as nulls via
        diagonal_relaxed concat and polars fills them in automatically.
        """
        src = self.source_dir
        log.info(" Loading and joining ARCHIVE CSV source files...")

        archive_package_df = pl.read_csv(
            Path(src, "ARCHIVE_PACKAGE.CSV"),
            separator=";",
            infer_schema_length=0,
        )

        # ARCHIVE_PRODUCT carries DISPENSINGTYPECODE and COMPANYID directly
        # (no separate PRODUCT_COMPANY join needed)
        archive_product_cols = pl.read_csv(
            Path(src, "ARCHIVE_PRODUCT.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(["ID", "DISPENSINGTYPECODE", "COMPANYID"])

        product_flag_cols = pl.read_csv(
            Path(src, "PRODUCT_FLAG.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(
            [
                "PRODUCTID",
                "CONTRACEPTIVE_FLAG",
                "COSMETICS_FLAG",
                "DIETARYSUPPLEMENT_FLAG",
                "HERBAL_FLAG",
                "GENERIC_FLAG",
                "HOMOEOPATHIC_FLAG",
            ]
        )

        item_df = pl.read_csv(
            Path(src, "ITEM.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(["ID", "PRODUCTID", "ITEMROACODE"])

        item_atc_df = pl.read_csv(
            Path(src, "ITEM_ATC.CSV"),
            separator=";",
            infer_schema_length=0,
        ).select(["ITEMID", "ATCCODE"])

        atc_per_product = (
            item_df.select(["ID", "PRODUCTID"])
            .join(item_atc_df, left_on="ID", right_on="ITEMID", how="left")
            .group_by("PRODUCTID")
            .agg(pl.col("ATCCODE").drop_nulls().unique())
        )

        roa_per_product = (
            item_df.select(["PRODUCTID", "ITEMROACODE"])
            .filter(pl.col("ITEMROACODE").is_not_null() & (pl.col("ITEMROACODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("ITEMROACODE").unique())
        )

        keywords_per_product = (
            pl.read_csv(
                Path(src, "PRODUCT_KEYWORD.CSV"),
                separator=";",
                infer_schema_length=0,
            )
            .select(["PRODUCTID", "CODE"])
            .filter(pl.col("CODE").is_not_null() & (pl.col("CODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("CODE").unique())
        )

        icd_per_product = (
            pl.read_csv(
                Path(src, "PRODUCT_ICD.CSV"),
                separator=";",
                infer_schema_length=0,
            )
            .select(["PRODUCTID", "ICDCODE"])
            .filter(pl.col("ICDCODE").is_not_null() & (pl.col("ICDCODE") != ""))
            .group_by("PRODUCTID")
            .agg(pl.col("ICDCODE").unique())
        )

        return (
            archive_package_df.join(
                archive_product_cols, left_on="PRODUCTID", right_on="ID", how="left"
            )
            .join(product_flag_cols, on="PRODUCTID", how="left")
            .join(atc_per_product, on="PRODUCTID", how="left")
            .join(roa_per_product, on="PRODUCTID", how="left")
            .join(keywords_per_product, on="PRODUCTID", how="left")
            .join(icd_per_product, on="PRODUCTID", how="left")
        )

    async def _parse_drug_data(
        self, drug_dataset_version: DrugDataSetVersion
    ) -> AsyncGenerator[Dict[type, List[Dict]], None]:
        log.info(" Building joined drug DataFrame...")
        joined_df = self._build_joined_dataframe()
        log.info(" Building joined archive drug DataFrame...")
        archive_df = self._build_archive_joined_dataframe()
        log.info(
            f" Combining {len(joined_df)} active and {len(archive_df)} archived drug packages..."
        )
        joined_df = pl.concat([joined_df, archive_df], how="diagonal_relaxed")

        if config.DRUG_DATA_IMPORT_MAX_ROWS:
            log.warning(
                f" Config var 'DRUG_DATA_IMPORT_MAX_ROWS' is set to {config.DRUG_DATA_IMPORT_MAX_ROWS}. We may not import all drug entries."
            )
            joined_df = joined_df.head(config.DRUG_DATA_IMPORT_MAX_ROWS)

        row_count_processing_max = len(joined_df)

        # Cache definitions once — not per-row
        code_defs = get_code_attr_definitions()
        attr_defs = get_attr_definitions()
        attr_ref_defs = get_attr_ref_definitions()
        attr_multi_defs = get_attr_multi_definitions()
        attr_multi_ref_defs = get_attr_multi_ref_definitions()

        log.info(f" Parse drug data ({row_count_processing_max} packages)...")
        debug_perf_start = time.time()

        for index, row in enumerate(joined_df.iter_rows(named=True)):
            if index % 10000 == 0:
                log.info(f" Processed {index} of {row_count_processing_max} packages")
            yield self._parse_drug_data_row(
                drug_dataset_version,
                row,
                code_defs,
                attr_defs,
                attr_ref_defs,
                attr_multi_defs,
                attr_multi_ref_defs,
            )

        total_time_sec = time.time() - debug_perf_start
        log.info(
            f" Time needed: {total_time_sec:.1f}s for {row_count_processing_max} drug entries."
        )

    def _parse_drug_data_row(
        self,
        drug_dataset_version: DrugDataSetVersion,
        row: Dict[str, Any],
        code_defs: List[DrugAttrFieldDefinitionContainer],
        attr_defs: List[DrugAttrFieldDefinitionContainer],
        attr_ref_defs: List[DrugAttrFieldDefinitionContainer],
        attr_multi_defs: List[DrugAttrFieldDefinitionContainer],
        attr_multi_ref_defs: List[DrugAttrFieldDefinitionContainer],
    ) -> Dict[type, List[Dict]]:
        drug_id = uuid.uuid4()
        drug_root_obj = {
            "id": drug_id,
            "source_dataset_id": drug_dataset_version.id,
            "is_custom_drug": False,
            "market_exit_date": None,
            "custom_drug_notes": None,
            "custom_created_by": None,
        }
        drug_objs: Dict[type, List[Dict]] = {
            DrugData: [drug_root_obj],
            DrugCode: [],
            DrugVal: [],
            DrugValRef: [],
            DrugValMulti: [],
            DrugValMultiRef: [],
        }

        for root_prop_name, mapping in root_props_mapping.items():
            drug_root_obj[root_prop_name] = self._cast_raw_csv_value_if_needed(
                row.get(mapping.colname), mapping
            )

        for code_def in code_defs:
            val = self._cast_raw_csv_value_if_needed(
                row.get(code_def.source_mapping.colname), code_def.source_mapping
            )
            if val is None:
                continue
            drug_objs[DrugCode].append(
                {
                    "id": uuid.uuid4(),
                    "drug_id": drug_id,
                    "code_system_id": code_def.field.id,
                    "code": val,
                }
            )

        for attr_def in attr_defs:
            drug_objs[DrugVal].append(
                {
                    "drug_id": drug_id,
                    "field_name": attr_def.field.field_name,
                    "value": self._cast_raw_csv_value_if_needed(
                        row.get(attr_def.source_mapping.colname),
                        attr_def.source_mapping,
                    ),
                    "importer_name": importername,
                }
            )

        for attr_ref_def in attr_ref_defs:
            val = self._cast_raw_csv_value_if_needed(
                row.get(attr_ref_def.source_mapping.colname),
                attr_ref_def.source_mapping,
            )
            if val is None:
                continue
            drug_objs[DrugValRef].append(
                {
                    "drug_id": drug_id,
                    "field_name": attr_ref_def.field.field_name,
                    "value": val,
                    "importer_name": importername,
                    "drug_dataset_version_fk": drug_dataset_version.id,
                }
            )

        for attr_multi_def in attr_multi_defs:
            raw_vals = row.get(attr_multi_def.source_mapping.colname) or []
            for idx, raw_val in enumerate(raw_vals):
                drug_objs[DrugValMulti].append(
                    {
                        "drug_id": drug_id,
                        "field_name": attr_multi_def.field.field_name,
                        "value": self._cast_raw_csv_value_if_needed(
                            raw_val, attr_multi_def.source_mapping
                        ),
                        "value_index": idx,
                        "importer_name": importername,
                    }
                )

        for attr_multi_ref_def in attr_multi_ref_defs:
            raw_vals = row.get(attr_multi_ref_def.source_mapping.colname) or []
            for idx, raw_val in enumerate(raw_vals):
                val = self._cast_raw_csv_value_if_needed(
                    raw_val, attr_multi_ref_def.source_mapping
                )
                if val is None:
                    continue
                drug_objs[DrugValMultiRef].append(
                    {
                        "drug_id": drug_id,
                        "field_name": attr_multi_ref_def.field.field_name,
                        "value": val,
                        "value_index": idx,
                        "importer_name": importername,
                        "drug_dataset_version_fk": drug_dataset_version.id,
                    }
                )

        return drug_objs

    def _cast_raw_csv_value_if_needed(self, value: Any, mapping: SourceAttrMapping):
        if value == "" or value is None:
            return None
        if mapping.cast_func:
            return mapping.cast_func(value)
        return str(value)

    async def _pg_copy_table(self, pg_conn, table_type: type, data: list[dict]) -> None:
        """Bulk-load a batch into a single PostgreSQL table via the COPY protocol.

        psycopg3 3.3+ exposes COPY on Cursor, not Connection. We open a cursor on
        the raw psycopg3 AsyncConnection and stream TSV in chunks of CHUNK rows so
        the in-memory buffer stays bounded.
        """
        table = table_type.__table__
        cols = [col.name for col in table.columns]
        col_list = ", ".join(cols)
        copy_stmt = f"COPY {table.name} ({col_list}) FROM STDIN"
        CHUNK = 50_000

        async with pg_conn.cursor() as cursor:
            async with cursor.copy(copy_stmt) as copy:
                buf: list[str] = []
                for row in data:
                    parts: list[str] = []
                    for col_name in cols:
                        val = row.get(col_name)
                        if val is None:
                            parts.append("\\N")
                        elif isinstance(val, bool):
                            parts.append("t" if val else "f")
                        else:
                            s = str(val)
                            s = (
                                s.replace("\\", "\\\\")
                                .replace("\t", "\\t")
                                .replace("\n", "\\n")
                                .replace("\r", "\\r")
                            )
                            parts.append(s)
                    buf.append("\t".join(parts) + "\n")
                    if len(buf) >= CHUNK:
                        await copy.write("".join(buf).encode("utf-8"))
                        buf.clear()
                if buf:
                    await copy.write("".join(buf).encode("utf-8"))

    async def add_and_flush(
        self, objs: List[SQLModel] = None, table_data: dict[type, list[dict]] = None
    ):
        session = self._db_session
        is_pg = config.SQL_DATABASE_URL.startswith("postgresql")

        if objs:
            log.debug(f" Flush {len(objs)} objects to database...")
            session.add_all(objs)
            await session.flush()
            objs.clear()

        if table_data:
            log.debug(" Write rows to database...")
            if is_pg:
                sa_conn = await session.connection()
                raw_conn = await sa_conn.get_raw_connection()
                pg_conn = raw_conn.driver_connection
                await session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
                for table_type, data in table_data.items():
                    if not data:
                        continue
                    log.debug(f" COPY {len(data)} '{table_type.__name__}' rows...")
                    await self._pg_copy_table(pg_conn, table_type, data)
            else:
                for table_type, data in table_data.items():
                    if not data:
                        continue
                    log.debug(
                        f" Bulk insert {len(data)} '{table_type.__name__}' rows..."
                    )
                    await session.execute(insert(table_type), data)
            await session.commit()
            table_data.clear()

    async def commit(self, objs=None):
        session = self._db_session
        if objs is not None:
            for obj in objs:
                session.add(obj)
        log.info(" Commit Drug data to database. This may take a while...")
        await session.commit()

    async def _generate_lov_items(
        self,
        paren_field: DrugValRef,
        lov_definition: MmiPiDrugAttrRefFieldLovImportDefinition,
        drug_dataset_version: DrugDataSetVersion,
    ) -> List[DrugAttrFieldLovItem]:
        lov_items: List[DrugAttrFieldLovItem] = []
        seen_values: set[str] = set()

        source_files = [lov_definition.lov_source_file] + list(
            lov_definition.additional_lov_source_files
        )

        def get_header_index(
            colname: str, headers: List[str], source_file: Path, default: Any = Unset
        ) -> int:
            try:
                return headers.index(colname)
            except (IndexError, ValueError):
                if default is not Unset:
                    return default
                raise ValueError(
                    f"[{self.__class__.__name__}] Could not find column '{colname}' in file '{source_file.resolve()}' while parsing LOV/Select/Reference-Values for field '{paren_field.field_name}'. \nExisting headers: {headers}"
                )

        for source_filename in source_files:
            source_file = Path(self.source_dir, source_filename)
            with open(source_file) as csvfile:
                csvreader = csv.reader(csvfile, delimiter=";")
                headers: List[str] = next(csvreader)

                for index, row in enumerate(csvreader):
                    value = row[get_header_index(lov_definition.values_col_name, headers, source_file)]
                    if value in seen_values:
                        continue
                    display_value = row[
                        get_header_index(lov_definition.display_value_col_name, headers, source_file)
                    ]
                    if lov_definition.display_name_factory:
                        display_value = lov_definition.display_name_factory(
                            paren_field.field_name, value, display_value
                        )
                    if lov_definition.filter_col is not None:
                        filter_col_index = get_header_index(
                            lov_definition.filter_col, headers, source_file, default=None
                        )
                        if row[filter_col_index] != lov_definition.filter_val:
                            continue

                    seen_values.add(value)
                    li = DrugAttrFieldLovItem(
                        field_name=paren_field.field_name,
                        value=value,
                        display=display_value,
                        sort_order=len(lov_items),
                        importer_name=importername,
                        drug_dataset_version_fk=drug_dataset_version.id,
                    )
                    lov_items.append(li)

        if lov_definition.sort_attr is not None:
            lov_items.sort(key=lambda obj: getattr(obj, lov_definition.sort_attr))
            for new_index, obj in enumerate(lov_items):
                obj.sort_order = new_index
        return lov_items
