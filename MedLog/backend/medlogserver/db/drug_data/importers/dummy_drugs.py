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
importername = "DummyDrugImporterV1"


@dataclass
class DrugAttrRefFieldLovImportDefinition:
    lov_source_file: str
    values_col_name: str
    display_value_col_name: str


@dataclass
class SourceAttrMapping:
    filename: str
    colname: str
    map2: str = None
    cast_func: Optional[Callable] = None

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
    lov: Optional[DrugAttrRefFieldLovImportDefinition] = None


drugs_csv_2_attr_mappings = {
    "trade_name": SourceAttrMapping(
        "drugs.csv",
        "NAME",
        map2="trade_name",
    ),
    "market_access_date": SourceAttrMapping(
        "drugs.csv",
        "MARKET_ACCESS_DATE",
        map2="market_access_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date(),
    ),
    "market_exit_date": SourceAttrMapping(
        "drugs.csv",
        "MARKET_EXIT_DATE",
        map2="market_exit_date",
        cast_func=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d").date(),
    ),
    # codes
    "codes.PZN": SourceAttrMapping(
        "drugs.csv",
        "PZN",
        map2="codes.PZN",
    ),
    "codes.ATC": SourceAttrMapping(
        "drugs.csv",
        "ATC",
        map2="codes.ATC",
    ),
    # attrs
    "attrs.amount": SourceAttrMapping(
        "drugs.csv",
        "AMOUNT",
        map2="attrs.amount",
    ),
    "attrs.manufacturer": SourceAttrMapping(
        "drugs.csv",
        "COMPANY",
        map2="attrs.manufacturer",
    ),
    "attrs.deliverysystem": SourceAttrMapping(
        "drugs.csv",
        "DELIVERYSYSTEM",
        map2="attrs.deliverysystem",
    ),
    "attrs.routeofadministration": SourceAttrMapping(
        "drugs.csv",
        "ROUTEOFADMINISTRATION",
        map2="attrs.routeofadministration",
    ),
    # ref attrs
    "attrs_ref.dispensingtype": SourceAttrMapping(
        "drugs.csv",
        "DISPENSINGTYPE_CODE",
        map2="attrs_ref.dispensingtype",
    ),
    # multi attrs
    "attrs_multi.keywords": SourceAttrMapping(
        "drugs.csv",
        "KEYWORD",
        map2="attrs_multi.keywords",
    ),
    # multi ref attrs
    "attrs_multi_ref.producing_country": SourceAttrMapping(
        "drugs.csv",
        "PROD_COUNTRY_CODE",
        map2="attrs_multi_ref.producing_country",
    ),
}


root_props_mapping = {
    prop_name: mapping
    for prop_name, mapping in drugs_csv_2_attr_mappings.items()
    if not "." in prop_name
}

code_attr_definitions = [
    DrugAttrFieldDefinitionContainer(
        field=DrugCodeSystem(
            id="ATC",
            name="ATC",
            country="International",
            desc="The Anatomical Therapeutic Chemical (ATC) Classification System is a drug classification system that classifies the active ingredients of drugs according to the organ or system on which they act and their therapeutic, pharmacological and chemical properties.",
            optional=True,
            unique=False,
        ),
        source_mapping=drugs_csv_2_attr_mappings["codes.ATC"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugCodeSystem(
            id="PZN",
            name="Pharmazentralnummer",
            country="Germany",
            optional=False,
            unique=True,
        ),
        source_mapping=drugs_csv_2_attr_mappings["codes.PZN"],
    ),
]


attr_definitions = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="amount",
            field_name_display="Amount",
            field_desc="Amount in package",
            value_type=ValueTypeCasting.FLOAT,
            optional=False,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=["10", "5.5", "80"],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs.amount"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="manufacturer",
            field_name_display="Manufacturer",
            field_desc="Manufacturing company of the drug",
            value_type=ValueTypeCasting.STR,
            optional=False,
            # default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=["PharamGigant", "MoneyMaker"],
            importer_name=importername,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs.manufacturer"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="deliverysystem",
            field_name_display="Delivery System",
            field_desc="Drug delivery refers to approaches, formulations, manufacturing techniques, storage systems, and technologies involved in transporting a pharmaceutical compound to its target site to achieve a desired therapeutic effect.",
            value_type=ValueTypeCasting.STR,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=["Spray", "Needle"],
            importer_name=importername,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs.deliverysystem"],
    ),
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="routeofadministration",
            field_name_display="Route of administration",
            field_desc="route of administration is the way by which a drug, fluid, poison, or other substance is taken into the body.",
            value_type=ValueTypeCasting.STR,
            optional=True,
            default=None,
            is_reference_list_field=False,
            is_multi_val_field=False,
            examples=["oral", "intravenous"],
            importer_name=importername,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs.routeofadministration"],
    ),
]


attr_multi_definitions: List[DrugAttrFieldDefinitionContainer] = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="keywords",
            field_name_display="Keywords",
            field_desc="How are the drugs made available.",
            value_type=ValueTypeCasting.STR,
            optional=False,
            # default=False,
            is_reference_list_field=False,
            is_multi_val_field=True,
            examples=["autoimmune", "suppress"],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs_multi.keywords"],
    )
]

# ref values packed together into a tuple with ref LOV import data
attr_ref_definitions: List[DrugAttrFieldDefinitionContainer] = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="dispensingtype",
            field_name_display="Dispensing Type",
            field_desc="How are the drugs made available.",
            value_type=ValueTypeCasting.INT,
            optional=False,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=False,
            examples=[1, 2],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs_ref.dispensingtype"],
        lov=DrugAttrRefFieldLovImportDefinition(
            lov_source_file="lov_DISPENSINGTYPE.csv",
            values_col_name="DISPENSINGTYPE_CODE",
            display_value_col_name="DISPENSINGTYPE",
        ),
    )
]

# ref values packed together into a tuple with ref LOV import data
attr_multi_ref_definitions: List[DrugAttrFieldDefinitionContainer] = [
    DrugAttrFieldDefinitionContainer(
        field=DrugAttrFieldDefinition(
            field_name="producing_country",
            field_name_display="Producing Country",
            field_desc="Country in which the manufacturer produces this drug",
            value_type=ValueTypeCasting.STR,
            optional=True,
            # default=False,
            is_reference_list_field=True,
            is_multi_val_field=True,
            examples=["DE", "UK"],
            importer_name=importername,
            searchable=True,
        ),
        source_mapping=drugs_csv_2_attr_mappings["attrs_multi_ref.producing_country"],
        lov=DrugAttrRefFieldLovImportDefinition(
            lov_source_file="lov_PROD_COUNTRY.csv",
            values_col_name="SHORT",
            display_value_col_name="NAME",
        ),
    ),
]


class DummyDrugImporterV1(DrugDataSetImporterBase):
    def __init__(self):

        self.dataset_name = "DummyDrugs"
        self.api_name = "dummydrugs"
        self.dataset_link = ""
        self.source_dir = None
        self.version = None
        self._attr_definitions = None
        self._attr_ref_definitions = None
        self._code_definitions = None
        self._lov_values: Dict[str, List[DrugAttrFieldLovItem]] = {}

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
        drug_data_objs: List[DrugData] = await self._parse_drug_data(drug_dataset)

        all_objs.extend(drug_data_objs)

        # write everything to database
        await self.commit(all_objs)

    async def _parse_drug_data(
        self, drug_dataset_version: DrugDataSetVersion
    ) -> List[
        DrugData | DrugVal | DrugValRef | DrugCode | DrugValMulti | DrugValMultiRef
    ]:

        log.info("[DRUG DATA IMPORT] Parse drug data...")
        drug_data_objs: List[DrugData] = []

        drugs_csv_path = Path(self.source_dir, "drugs.csv")
        with open(drugs_csv_path, "rt") as drugs_csc_file:
            drugs_csv = csv.reader(drugs_csc_file, delimiter=";")
            drugs_csv_headers = next(drugs_csv)
            for index, drugs_row in enumerate(drugs_csv):
                drug_data_objs.append(
                    await self._parse_drug_data_drugs_row(
                        drug_dataset_version, drugs_row, drugs_csv_headers
                    )
                )
        # print("drug_data_objs", drug_data_objs)
        return drug_data_objs

    async def _parse_drug_data_drugs_row(
        self,
        drug_dataset_version: DrugDataSetVersion,
        drug_row: List[str],
        drug_row_headers: List[str],
    ) -> DrugData:
        result_drug_data = DrugData(source_dataset=drug_dataset_version)
        # drug root attrs
        for root_prop_name, mapping in root_props_mapping.items():
            drug_attr_value = drug_row[drug_row_headers.index(mapping.colname)]
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, mapping
            )
            setattr(result_drug_data, root_prop_name, drug_attr_value)
        # drug codes
        for drug_code_data in code_attr_definitions:
            drug_code_value = drug_row[
                drug_row_headers.index(drug_code_data.source_mapping.colname)
            ]
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
            drug_attr_value = drug_row[
                drug_row_headers.index(attr_data.source_mapping.colname)
            ]
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, attr_data.source_mapping
            )
            await self._validate_csv_value(
                value=drug_attr_value, mapping=attr_data.source_mapping
            )
            result_drug_data.attrs.append(
                DrugVal(
                    field_name=attr_data.field.field_name,
                    value=drug_attr_value,
                    importer_name=importername,
                )
            )
        # drug ref attr
        for attr_ref_data in attr_ref_definitions:
            drug_attr_value = drug_row[
                drug_row_headers.index(attr_ref_data.source_mapping.colname)
            ]
            drug_attr_value = self._cast_raw_csv_value_if_needed(
                drug_attr_value, attr_ref_data.source_mapping
            )
            await self._validate_csv_value(
                value=drug_attr_value, mapping=attr_ref_data.source_mapping
            )

            result_drug_data.attrs_ref.append(
                DrugValRef(
                    field_name=attr_ref_data.field.field_name,
                    value=drug_attr_value,
                    importer_name=importername,
                )
            )
        # drug multi attrs
        for attr_multi_data in attr_multi_definitions:
            drug_attr_values = drug_row[
                drug_row_headers.index(attr_multi_data.source_mapping.colname)
            ].split(",")
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
                        importer_name=importername,
                    )
                )
        # drug multi ref attrs
        for attr_multi_ref_data in attr_multi_ref_definitions:
            drug_attr_values = drug_row[
                drug_row_headers.index(attr_multi_ref_data.source_mapping.colname)
            ].split(",")
            for index, drug_attr_val in enumerate(drug_attr_values):
                drug_attr_val = self._cast_raw_csv_value_if_needed(
                    drug_attr_val, attr_multi_ref_data.source_mapping
                )
                await self._validate_csv_value(
                    value=drug_attr_val, mapping=attr_multi_ref_data.source_mapping
                )
                result_drug_data.attrs_multi_ref.append(
                    DrugValMultiRef(
                        field_name=attr_multi_ref_data.field.field_name,
                        value=drug_attr_val,
                        value_index=index,
                        importer_name=importername,
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
        if target_attr_def.is_reference_list_field:
            ref_value_exists = False
            for lov_item in self._lov_values[attr_name]:
                if lov_item.value == value:
                    ref_value_exists = True
                    break
            if not ref_value_exists:
                raise ValueError(
                    f"Reference object for {mapping_attr} does not exists for value {value}. '{self._lov_values[attr_name]}'\n{self._lov_values}"
                )
        try:
            target_attr_def.value_type.value.casting_func(value)
        except:
            raise ValueError(
                f"Could not cast raw value '{value}' to type {target_attr_def.value_type.value.python_type} as defined in {target_attr_def}. "
            )

    async def commit(self, objs):
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
        lov_definition: DrugAttrRefFieldLovImportDefinition,
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

                li = DrugAttrFieldLovItem(
                    field_name=paren_field.field_name,
                    value=value,
                    display=display_value,
                    sort_order=index,
                    importer_name=importername,
                )
                lov_items.append(li)

        return lov_items
