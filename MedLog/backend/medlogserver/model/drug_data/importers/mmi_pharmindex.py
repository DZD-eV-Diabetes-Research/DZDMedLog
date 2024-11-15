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
    packageid_path: Optional[str] = (
        None  # if a mmi source table has no direkt product id we need path to map the product id. must start with  a column from the "filename" csv file and end with PRODUCT ID. e.g. "ITEM_ATC.CSV[ITEMID]/ITEM.CSV[ID]>[PRODUCTID]"
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
        "root", "attrs", "multi_attrs", "ref_attrs", "ref_multi_attrs", "codes"
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
            "multi_attrs": DrugValMulti,
            "ref_attrs": DrugValRef,
            "ref_multi_attrs": DrugValMultiRef,
            "codes": DrugCode,
        }
        return map[t]


mmi_rohdaten_r3_mappings = [
    SourceAttrMapping(
        "PACKAGE.CSV",
        "NAME",
        packageid_path="PACKAGE.CSV[ID]",
        map2="trade_name",
    ),
    SourceAttrMapping(
        "PACKAGE.CSV",
        "ONMARKETDATE",
        packageid_path="PACKAGE.CSV[ID]",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%d.%m.%Y").date(),
    ),
    ## FileProductMapping(map2="market_exit_date"), # exited drugs are in an extra file :/ we will fix that later
    # codes
    SourceAttrMapping(
        "PACKAGE.CSV",
        "PZN",
        packageid_path="PACKAGE.CSV[ID]",
        map2="codes.PZN",
    ),
    SourceAttrMapping(
        "PACKAGE.CSV",
        "PRODUCTID",
        packageid_path="PACKAGE.CSV[ID]",
        map2="codes.MMIP",
    ),
    SourceAttrMapping(
        "ITEM_ATC.CSV",
        "ATCCODE",
        packageid_path="ITEM_ATC.CSV[ITEMID]/ITEM.CSV[ID]>[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="codes.ATC",
    ),
    # attrs
    SourceAttrMapping(
        "PACKAGE.CSV",
        "AMOUNTTEXT",
        packageid_path="PACKAGE.CSV[ID]",
        map2="attrs.amount",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "CONTRACEPTIVE_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_verhuetungsmittel",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "COSMETICS_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_kosmetikum",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "DIETARYSUPPLEMENT_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_nahrungsergaenzungsmittel",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HERBAL_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_pflanzlich",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "GENERIC_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_generikum",
    ),
    SourceAttrMapping(
        "PRODUCT_FLAG.CSV",
        "HOMOEOPATHIC_FLAG",
        packageid_path="PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="attrs.ist_homoeopathisch",
    ),
    # ref attrs
    SourceAttrMapping(
        "PACKAGE.CSV",
        "IFAPHARMFORMCODE",
        packageid_path="PACKAGE.CSV[ID]",
        map2="ref_attrs.darreichungsform",  # Im Vertrieb, Rückruf,... catalog ref id 109
    ),
    SourceAttrMapping(
        "PACKAGE.CSV",
        "SALESSTATUSCODE",
        packageid_path="PACKAGE.CSV[ID]",
        map2="ref_attrs.vertriebsstatus",  # Im Vertrieb, Rückruf,... catalog ref id 116
    ),
    SourceAttrMapping(
        "PACKAGE.CSV",
        "PACKAGENORMSIZECODE",
        packageid_path="PACKAGE.CSV[ID]",
        map2="ref_attrs.normgroesse",  # N0, N1,... catalog ref id 117
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "DISPENSINGTYPECODE",
        packageid_path="PRODUCT.CSV[ID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_attrs.abgabestatus",  # rezeptpflichtig, apothenkenpflichtig,... catalog ref id 119
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTFOODTYPECODE",
        packageid_path="PRODUCT.CSV[ID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_attrs.lebensmittel",  # ja, nein, sonstiges ,... catalog ref id 205
    ),
    SourceAttrMapping(
        "PRODUCT.CSV",
        "PRODUCTDIETETICSTYPECODE",
        packageid_path="PRODUCT.CSV[ID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_attrs.diaetetikum",  # ja, nein, sonstiges ,... catalog ref id 206
    ),
    SourceAttrMapping(
        "PRODUCT_COMPANY.CSV",
        "COMPANYID",
        packageid_path="PRODUCT_COMPANY.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_attrs.hersteller",
        filter_colname="PRODUCTCOMPANYTYPECODE",
        filter_colval="M",  # only "hersteller" no "mitvertriebler". other wise we get multiple hersteller per product
    ),
    # multi ref attrs
    SourceAttrMapping(
        "ITEM.CSV",
        "ITEMROACODE",
        packageid_path="ITEM.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_multi_attrs.applikationsart",  # Im Vertrieb, Rückruf,... catalog ref id 123
    ),
    SourceAttrMapping(
        "PRODUCT_KEYWORD.CSV",
        "CODE",
        packageid_path="PRODUCT_KEYWORD.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",
        map2="ref_multi_attrs.keywords",  # no catalog id. seperate csv named KEYWORD.CSV
    ),
    SourceAttrMapping(
        "PRODUCT_ICD.CSV",
        "ICDCODE",
        map2="ref_multi_attrs.icd10",
        packageid_path="PRODUCT_ICD.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]",  # icd10 code,... catalog ref id 18
    ),
]
""" I can not grasp the DDD in mmi pharmindex. there is only a DDD per Arzneimittelvereinbarungen (AVR) but that makes no sense for me. Lets keep that stuff out for now.
    SourceAttrMapping(
        "ARV_PACKAGEGROUP.CSV",
        "DDDAMOUNT",
        packageid_path="ARV_PACKAGEGROUP.CSV[PACKAGEID]",
        map2="attrs.ddd",
    ),
"""
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
        id="MMIP",
        name="MMI Product ID",
        country="Internal",
        desc="Interne 'PRODUCTID' des Vidal MMI Pharmindex",
        optional=False,
        unique=False,
    ),
]
importername = "MmmiPharmaindex1_32"


attr_definitions = [
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
    DrugAttrFieldDefinition(
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
]
""" I can not grasp the DDD in mmi pharmindex. there is only a DDD per Arzneimittelvereinbarungen (AVR) but that makes no sense for me. Lets keep that stuff out for now.
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
"""

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
            display_value_col_name="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
]

# ref values packed together into a tuple with ref LOV import data
multi_ref_attr_definitions: List[DrugRefAttrLovFieldDefinitionContainer] = [
    DrugRefAttrLovFieldDefinitionContainer(
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
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
            filter_val="123",
        ),
    ),
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
            values_col_name="CODE",
            display_value_col_name="NAME",
            filter_col=None,
            filter_val=None,
        ),
    ),
    DrugRefAttrLovFieldDefinitionContainer(
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
        lov=MmiPiDrugRefAttrFieldLovImportDefinition(
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

    async def run_import(self, source_dir: Path, version: str):
        # generate schema definitions; fields,lov-defintions,...
        raise NotImplementedError(
            "You are here monday-tim. proto done but some values are missing in db and some value not bubling up the api. its still a mess, sorry man, cheers friday-tim :)"
        )
        log.info("[DRUG DATA IMPORT] Parse metadata...")
        all_objs = []
        drug_dataset = await self._ensure_drug_dataset_version()
        # generate list of values
        attr_defs = attr_definitions + multi_attr_definitions
        all_objs.extend(attr_defs)
        for ref_lov_field_obj in ref_attr_definitions + multi_ref_attr_definitions:
            all_objs.append(ref_lov_field_obj.field)
            all_objs.extend(
                await self._generate_lov_items(
                    ref_lov_field_obj.field, lov_definition=ref_lov_field_obj.lov
                )
            )

        # read all drugs with attributes
        drug_data_objs = await self._parse_drug_data(drug_dataset)

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
        multi_val_indexes: Dict[str, Dict[str, int]] = {}
        #
        # Parse mapped attrs
        #
        attr_mappings = [
            m for m in mmi_rohdaten_r3_mappings if m.drug_attr_type_name != "codes"
        ]
        for mapping in attr_mappings:
            async for packageid, drug_val in self._parse_drug_attr_data(
                mapping, drug_dataset_version
            ):
                if (
                    isinstance(drug_val, DrugModelTableBase) and drug_val.value in [""]
                ) or drug_val in [""]:
                    # clean empty string to 'None's
                    drug_val.value = None

                if packageid not in drug_data_objs:
                    drug_data_objs[packageid] = DrugData(
                        source_dataset=drug_dataset_version
                    )
                    multi_val_indexes[packageid] = {}
                if isinstance(drug_val, (DrugValMulti | DrugValMultiRef)):
                    if drug_val.value is not None:
                        # no empty multi values
                        continue

                    # we need to give multi vals a sequence/index
                    if mapping.drug_attr_name not in multi_val_indexes[packageid]:
                        multi_val_indexes[packageid][mapping.drug_attr_name] = 0
                    drug_val.value_index = multi_val_indexes[packageid][
                        mapping.drug_attr_name
                    ]
                    multi_val_indexes[packageid][mapping.drug_attr_name] += 1

                # Attch the attr/val-objects to a drug object
                if isinstance(drug_val, DrugVal):
                    drug_data_objs[packageid].attrs.append(drug_val)
                elif isinstance(drug_val, DrugValRef):
                    drug_data_objs[packageid].ref_attrs.append(drug_val)
                elif isinstance(drug_val, DrugValMulti) and drug_val is not None:
                    drug_data_objs[packageid].multi_attrs.append(drug_val)
                elif isinstance(drug_val, DrugValMultiRef) and drug_val is not None:
                    drug_data_objs[packageid].ref_multi_attrs.append(drug_val)
                else:
                    # root attrs
                    setattr(drug_data_objs[packageid], mapping.drug_attr_name, drug_val)
        #
        # Parse Drug Codes
        #

        # finsihed parsing
        """
        log.warning(
            "Todo: This is just a fix for making the demo dataset work. remove when we got the real data"
        )
        for packageid, obj in drug_data_objs.items():
            if not obj.trade_name:
                print(packageid, obj)
        print("COUNT", len(drug_data_objs))
        exit()
        drug_data_objs = {
            pid: dobj for pid, dobj in drug_data_objs.items() if dobj.trade_name
        }
        """

        # for packageid, drug_data_o in drug_data_objs.items():
        #    if drug_data_o.trade_name is None:
        #        print("MÖP! WRONG! trade_name none is not allowed", packageid, drug_data_o)
        #        exit()
        return list(drug_data_objs.values())

    async def _parse_drug_attr_data(
        self,
        attr_mapping: SourceAttrMapping,
        drug_dataset_version: DrugDataSetVersion,
    ) -> AsyncIterator[
        Tuple[str, str | DrugVal | DrugValRef | DrugValMulti | DrugValMultiRef]
    ]:
        # raise NotImplementedError(
        #    "You are here. You need to parse SourceAttrMapping.cast_func into account. We dont use it yet, which lead to impoer errors"
        # )
        source_file = Path(self.source_dir, attr_mapping.filename)
        with open(source_file, "rt") as src_file:
            csvreader = csv.reader(src_file, delimiter=";")
            headers: List[str] = next(csvreader)
            # log.info(("attr_mapping", attr_mapping))
            value_col_index = headers.index(attr_mapping.colname)
            key_col = "PACKAGEID"
            if attr_mapping.packageid_path is not None:
                # e.g. ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]
                # we need the first key for now. e.g. "PACKAGEID"
                # Use regular expression to find the first occurrence of a value inside the square brackets
                # and therefore the root id column
                key_col = extract_bracket_values(attr_mapping.packageid_path, 1)[0]
            try:
                key_col_index = headers.index(key_col)
            except:
                raise ValueError(
                    f"[{self.__class__.__name__}] Can not find col '{key_col}' in file '{source_file.resolve()}' for attribute mapping '{attr_mapping}'. There is probaly a source data error or a bug in the attribute mapping."
                )
            filter_col_index = None
            if attr_mapping.filter_colname is not None:
                filter_col_index = headers.index(attr_mapping.filter_colname)
            for row in csvreader:
                raw_val = row[value_col_index]
                key_val = row[key_col_index]
                if (
                    filter_col_index is not None
                    and row[filter_col_index] != attr_mapping.filter_colval
                ):
                    continue

                if attr_mapping.packageid_path:
                    # we need to hop some multiple CSVs to lookup the referenced productid
                    packageid = await self._packageid_lookup_by_path(
                        row, headers, attr_mapping.packageid_path
                    )
                else:
                    packageid = key_val
                if attr_mapping.cast_func is not None:
                    drug_attr_value = attr_mapping.cast_func(raw_val)
                else:
                    drug_attr_value = raw_val
                if attr_mapping.drug_attr_type_name == "root":
                    yield (key_val, drug_attr_value)
                    continue
                DrugValModel: (
                    Type[DrugVal]
                    | Type[DrugValRef]
                    | Type[DrugValMulti]
                    | Type[DrugValMultiRef]
                ) = attr_mapping.drug_attr_type

                valInstance = DrugValModel(
                    field_name=attr_mapping.drug_attr_name, value=drug_attr_value
                )

                yield (packageid, valInstance)

    async def _get_row_with_header_from_csv_file(
        self, id_col_name: str, id_col_val, file_path: Path
    ) -> Tuple[List[str], List[str]]:
        with open(file_path, "rt") as file:
            csvreader = csv.reader(file, delimiter=";")
            headers = next(csvreader)
            id_col_index = headers.index(id_col_name)
            for row in csvreader:
                if row[id_col_index] == id_col_val:
                    return headers, row

    async def _packageid_lookup_by_path(
        self, row: List[str], row_headers: List[str], key_path: str, _fragment_pos=0
    ) -> str:
        """
        Recursively traverses CSV files to find and return the `PACKAGEID` associated
        with a given starting key value. This function follows a path defined in `key_path`
        (`key_path` itself comes from SourceAttrMapping.packageid_path)
        through multiple CSV files, where each segment of the path specifies a CSV file,
        the lookup key, and target key within that file.

        Args:
            row (List[str]): The CSV row to start the lookup from
            row_headers (List[str]): The header for the row to identify columns
            key_path (str): A string defining the path of files and keys to follow for
                            retrieving the `PACKAGEID`. The path segments are in the format
                            `<filename>[<entry_column>]/<next_filename>[<target_column>]...`
                            and should end with the package id (usally `[PACKAGEID]` or `[ID]` in the final segment,
                            indicating the desired field.

        Raises:
            ValueError: If the `key_path` is invalid or does not contain the expected
                        structure of filenames and column names in brackets.
            ValueError: If an entry column or target column is missing or misformatted
                        within a path segment.

        Returns:
            str: The `PACKAGEID` linked to the initial `start_key_val`, based on the
                specified `key_path`.

        Example:
            # Suppose key_path = "PRODUCT_FLAG.CSV[PRODUCTID]/PACKAGE.CSV[PRODUCTID]>[ID]"
            # This will:
            # 1. Look up `PRODUCTID` in `PRODUCT_FLAG.CSV` for the row.
            # 2. Finally, return the PackageID column `ID` from `PACKAGE.CSV`
        """
        # e.g. key_path="ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]"
        # ToDo: This function does way too much at once at low efficiency (which also is the story of this complete class :D ). But before optimizing here, rethink the whole importer architecture
        current_path_fragment = key_path.split("/")[0]
        path_without_current_fragment = "/".join(key_path.split("/")[1:])
        file_name = current_path_fragment.split("[")[0]
        file_path = Path(self.source_dir, file_name)
        is_last_fragment = len(key_path.split("/")) == 1
        is_first_path_fragment = _fragment_pos == 0
        is_single_fragment_path = is_first_path_fragment and is_last_fragment

        if is_single_fragment_path:
            # the packageid is in the row/file itself. no need for forther digging
            # we can just return the value of the correct column from the current row
            # e.g. key_path is "PACKAGE.CSV[ID]"
            current_target_col = extract_bracket_values(current_path_fragment, count=1)[
                0
            ]
            target_val = row[row_headers.index(current_target_col)]
            return target_val
        if is_first_path_fragment:
            # this is the entry path node
            current_target_col = extract_bracket_values(current_path_fragment, count=1)[
                0
            ]
            next_target_col = extract_bracket_values(key_path, count=2)[1]
            target_val = row[row_headers.index(current_target_col)]
            next_lookup_file_name = path_without_current_fragment.split("[")[0]
            next_lookup_file = Path(self.source_dir, next_lookup_file_name)
            next_lookup_row_with_headers = (
                await self._get_row_with_header_from_csv_file(
                    id_col_name=next_target_col,
                    id_col_val=target_val,
                    file_path=next_lookup_file,
                )
            )
            if next_lookup_row_with_headers is None:
                raise ValueError(
                    f"[{self.__class__.__name__}] Could not find row with value '{target_val}' in column '{current_target_col}' in file '{next_lookup_file_name}' for key_path fragment '{current_path_fragment}' in key_path '{key_path}'"
                )
            return await self._packageid_lookup_by_path(
                next_lookup_row_with_headers[1],
                row_headers=next_lookup_row_with_headers[0],
                key_path=path_without_current_fragment,
                _fragment_pos=_fragment_pos + 1,
            )

        try:
            current_entry_col, current_target_col = extract_bracket_values(
                current_path_fragment, count=2
            )
        except ValueError as e:
            raise ValueError(
                f"[{self.__class__.__name__}] Could not resolve 'SourceAttrMapping.productid_ref_path' fragment '{current_path_fragment}' (from path '{key_path}'). Expected path with at least 2 column names in brackets (e.g. 'PACKAGE.CSV[ID]>[PRODUCTID]'). Got '{current_path_fragment}'"
            )
        target_col_index = row_headers.index(current_target_col)
        if is_last_fragment:
            return row[target_col_index]
        else:
            target_val = row[target_col_index]
            next_target_col = extract_bracket_values(key_path, count=2)[1]

            next_lookup_file_name = path_without_current_fragment.split("[")[0]
            next_lookup_file = Path(self.source_dir, next_lookup_file_name)
            next_lookup_row_with_headers = (
                await self._get_row_with_header_from_csv_file(
                    id_col_name=next_target_col,
                    id_col_val=target_val,
                    file_path=next_lookup_file,
                )
            )
            return await self._packageid_lookup_by_path(
                next_lookup_row_with_headers[1],
                row_headers=next_lookup_row_with_headers[0],
                key_path=path_without_current_fragment,
                _fragment_pos=_fragment_pos + 1,
            )

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
        lov_definition: MmiPiDrugRefAttrFieldLovImportDefinition,
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
