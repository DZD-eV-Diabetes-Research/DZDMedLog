"""Column layout of the study export (issue #387).

The CSV export used to build its header from the columns of the exported rows, so the
drug columns depended on which drugs a study referenced. The layout here is built from
the export models and the field definitions of the configured drug importer instead,
which makes every export of an installation have the same columns in the same order.

All column names are built by `export_column_name()`. The CSV export and the export
schema use this module, so the two cannot drift apart.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple, Type
from dataclasses import dataclass
from pydantic import BaseModel, field_serializer, model_serializer

from medlogserver.model import (
    IntakeExport,
    EventExport,
    StudyExport,
    InterviewExport,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
    ValueTypeCasting,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.db.drug_data.importers.mmi_pharmindex import (
    importername as MMI_PHARMINDEX_IMPORTER_NAME,
)
from medlogserver.db.drug_data.importers._base import DrugDataSetImporterBase
from medlogserver.config import Config

config = Config()


class DrugCodesExport(BaseModel):
    drug_code_system_id: str
    drug_code_system_name: str
    drug_code: str


class ValueReferenceCodeNotApplicable:
    pass


class DrugDataExport(BaseModel):
    drug_attr_name: str
    drug_attr_value: bool | str | List[bool | str | None] | None
    drug_attr_reference_code: (
        str | List[str | None] | None | Type[ValueReferenceCodeNotApplicable]
    ) = ValueReferenceCodeNotApplicable

    # Attributes that are not references (e.g. `trade_name`) have no reference code.
    # The key is left out instead of being written as null. The CSV export skips
    # these columns the same way. Before, `model_dump_json()` failed on the marker
    # class, so the JSON export of any study with intakes died with
    # "Unable to serialize unknown type: <class 'type'>".
    @field_serializer("drug_attr_reference_code")
    def _serialize_reference_code(self, value):
        return None if value is ValueReferenceCodeNotApplicable else value

    @model_serializer(mode="wrap")
    def _omit_not_applicable_reference_code(self, handler):
        data = handler(self)
        if self.drug_attr_reference_code is ValueReferenceCodeNotApplicable:
            data.pop("drug_attr_reference_code", None)
        return data


# The export objects that are the same for every installation, as
# (column prefix, model), in CSV column order.
FIXED_EXPORT_OBJECTS: List[Tuple[str, Type[BaseModel]]] = [
    ("study", StudyExport),
    ("event", EventExport),
    ("interview", InterviewExport),
    ("intake", IntakeExport),
]

# Drug attributes every drug has, independent of the drug importer.
# See `drug_to_export_data()`.
FIXED_DRUG_ATTR_NAMES: List[str] = [
    "trade_name",
    "market_access_date",
    "market_exit_date",
    "is_custom_drug",
    "custom_drug_notes",
]

# Fixed drug attributes with a boolean value. Importer attributes are boolean when
# their field definition has `value_type` BOOL (issue #389).
FIXED_BOOL_DRUG_ATTR_NAMES: set[str] = {"is_custom_drug"}

# Reference attributes whose reference code only repeats the display value, e.g. MMI
# `lebensmittel` "N" next to "Nein". They get no reference code (issue #389).
# Keyed by (importer_name, field_name).
REDUNDANT_REFERENCE_CODE_FIELDS: set[Tuple[str, str]] = {
    (MMI_PHARMINDEX_IMPORTER_NAME, "diaetetikum"),
    (MMI_PHARMINDEX_IMPORTER_NAME, "lebensmittel"),
}

DrugAttrKind = Literal["fixed", "attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref"]


def export_column_name(
    obj_name: str, prop_name: str, pivot_value: Optional[str] = None
) -> str:
    """Name of the CSV column for property `prop_name` of export object `obj_name`.

    Properties are prefixed with the object name unless they already start with it
    (`id` of the study becomes `study_id`, `intake_start_date` stays as it is). Pivoted
    list items (drug codes, drug attributes) get the lowercased pivot value as suffix,
    e.g. `drug_attr_value_trade_name`.
    """
    column_name = prop_name if prop_name.startswith(obj_name) else f"{obj_name}_{prop_name}"
    if pivot_value is not None:
        column_name = f"{column_name}_{pivot_value}".lower()
    return column_name


def flatten_export_objects(
    objs: BaseModel | List[BaseModel],
    obj_name: str,
    pivot_by_column: str | None = None,
    exclude: set[str] | None = None,
) -> Dict[str, Any]:
    """Turn one export object (or a list of them) into flat CSV columns.

    Lists are pivoted: every item becomes its own set of columns, suffixed with the
    value of `pivot_by_column` (e.g. one `drug_code_<system>` column per code system).
    Properties in `exclude` get no column.
    """
    columns: Dict[str, Any] = {}
    if not isinstance(objs, list):
        objs = [objs]
    exclude_set = set(exclude or ())
    if pivot_by_column:
        exclude_set.add(pivot_by_column)
    for obj in objs:
        pivot_value = getattr(obj, pivot_by_column) if pivot_by_column else None
        for prop_name, prop_value in obj.model_dump(exclude=exclude_set).items():
            columns[export_column_name(obj_name, prop_name, pivot_value)] = prop_value
    return columns


def flatten_export_drug_codes(drug_codes: List[DrugCodesExport]) -> Dict[str, Any]:
    # One column per code system, named by the code system id (`drug_code_pzn`).
    # The display name contains spaces for some systems ("MMI Product ID"), which made
    # awkward column names (issue #389).
    return flatten_export_objects(
        drug_codes,
        "drug_code",
        "drug_code_system_id",
        exclude={"drug_code_system_name"},
    )


def model_export_properties(model: Type[BaseModel]) -> List[str]:
    """The property names `model.model_dump()` writes, without needing an instance.

    The serialization schema leaves out excluded fields and includes computed fields,
    the same as `model_dump()`.
    """
    return list(model.model_json_schema(mode="serialization")["properties"])


@dataclass
class ExportDrugAttr:
    name: str
    kind: DrugAttrKind
    # None for the `FIXED_DRUG_ATTR_NAMES`
    field_definition: Optional[DrugAttrFieldDefinition] = None

    @property
    def is_reference(self) -> bool:
        return self.kind in ("attrs_ref", "attrs_multi_ref")

    @property
    def is_multi(self) -> bool:
        return self.kind in ("attrs_multi", "attrs_multi_ref")

    @property
    def is_bool(self) -> bool:
        if self.field_definition is None:
            return self.name in FIXED_BOOL_DRUG_ATTR_NAMES
        return (
            ValueTypeCasting(self.field_definition.value_type) is ValueTypeCasting.BOOL
        )

    @property
    def has_reference_code(self) -> bool:
        return self.is_reference and (
            self.field_definition.importer_name,
            self.name,
        ) not in REDUNDANT_REFERENCE_CODE_FIELDS

    @property
    def value_column(self) -> str:
        return export_column_name("drug", "drug_attr_value", self.name)

    @property
    def reference_code_column(self) -> Optional[str]:
        if not self.has_reference_code:
            return None
        return export_column_name("drug", "drug_attr_reference_code", self.name)

    def empty_export(self) -> DrugDataExport:
        """The export entry for a drug that has no value for this attribute."""
        return DrugDataExport(
            drug_attr_name=self.name,
            drug_attr_value=None,
            drug_attr_reference_code=(
                None if self.has_reference_code else ValueReferenceCodeNotApplicable
            ),
        )


class ExportLayout:
    """All columns an export of this installation can have, in a fixed order.

    Order: study, event, interview and intake columns (model field order), then one
    `drug_code_<system>` column per code system in code definition order, then the
    drug attributes: `FIXED_DRUG_ATTR_NAMES`, then the importer's attrs, attrs_ref,
    attrs_multi and attrs_multi_ref, each in field definition order. A reference
    attribute has its value column directly followed by its reference code column,
    unless the code only repeats the value (`REDUNDANT_REFERENCE_CODE_FIELDS`).
    """

    def __init__(
        self, code_systems: List[DrugCodeSystem], drug_attrs: List[ExportDrugAttr]
    ):
        self.code_systems = code_systems
        self.drug_attrs = drug_attrs
        self.drug_attrs_by_name: Dict[str, ExportDrugAttr] = {
            attr.name: attr for attr in drug_attrs
        }

    @classmethod
    async def from_importer(
        cls, importer: Optional[DrugDataSetImporterBase] = None
    ) -> "ExportLayout":
        """Layout for `importer`, default: the configured `DRUG_IMPORTER_PLUGIN`.

        The field definitions are defined in code, this does not access the database.
        """
        if importer is None:
            importer = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]()
        field_definitions = await importer.get_all_attr_field_definitions()
        drug_attrs = [ExportDrugAttr(name, "fixed") for name in FIXED_DRUG_ATTR_NAMES]
        kind: DrugAttrKind
        for kind in ("attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref"):
            for field_definition in field_definitions[kind]:
                drug_attrs.append(
                    ExportDrugAttr(
                        name=field_definition.field_name,
                        kind=kind,
                        field_definition=field_definition,
                    )
                )
        return cls(code_systems=field_definitions["codes"], drug_attrs=drug_attrs)

    def fixed_columns(self) -> List[str]:
        columns: Dict[str, None] = {}
        for obj_name, model in FIXED_EXPORT_OBJECTS:
            for prop_name in model_export_properties(model):
                columns[export_column_name(obj_name, prop_name)] = None
        return list(columns)

    def drug_code_columns(self) -> List[str]:
        return [
            export_column_name("drug_code", "drug_code", code_system.id)
            for code_system in self.code_systems
        ]

    def drug_attr_columns(self) -> List[str]:
        columns: List[str] = []
        for attr in self.drug_attrs:
            columns.append(attr.value_column)
            if attr.has_reference_code:
                columns.append(attr.reference_code_column)
        return columns

    def csv_columns(self) -> List[str]:
        """The CSV header. Every CSV export of this installation has these columns."""
        return list(
            dict.fromkeys(
                self.fixed_columns()
                + self.drug_code_columns()
                + self.drug_attr_columns()
            )
        )

    def complete_drug_attrs(
        self, attrs: List[DrugDataExport]
    ) -> List[DrugDataExport]:
        """`attrs` in layout order, with an empty entry for every missing attribute.

        Attributes that are not in the layout (should not happen, the drug data is
        written by the same importer) are kept and appended at the end.
        """
        attrs_by_name = {attr.drug_attr_name: attr for attr in attrs}
        completed = [
            attrs_by_name.pop(layout_attr.name, None) or layout_attr.empty_export()
            for layout_attr in self.drug_attrs
        ]
        completed.extend(attrs_by_name.values())
        return completed
