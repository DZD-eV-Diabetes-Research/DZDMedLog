"""Schemas of the study export (issue #387, part 2).

* JSON export: a JSON Schema (https://json-schema.org/, draft 2020-12)
* CSV export: a Frictionless Table Schema (https://datapackage.org/standard/table-schema/, v2)

Both are built from `ExportLayout`, the same column list the exporter uses, plus the
reference list values of the imported drug datasets. The functions here do not access
the database; the reference values are passed in (see `export_schema_build.py`).

What the export really writes, and the schemas therefore describe:

* All drug attribute values are written as strings, whatever their `value_type`. The
  importers store the raw source value and only check that it can be cast. The JSON
  Schema types them as strings and names the value type in the description, the
  Table Schema maps the value type to a column type.
* The CSV export writes Python values with `str()`: booleans as `True`/`False`,
  datetimes as `YYYY-MM-DD HH:MM:SS[.ffffff]`, missing values as empty cells.
* Multi value drug attributes are written to the CSV as Python list reprs, e.g.
  `['a', None]`. They can only be typed as string (known limitation, see the issue).
"""

from typing import Any, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema
from pydantic_core import core_schema

from medlogserver.model.drug_data.drug_attr_field_definition import ValueTypeCasting
from medlogserver.model.export_schema import ExportSchemaFormat
from medlogserver.worker.tasks.export_layout import (
    FIXED_EXPORT_OBJECTS,
    ExportDrugAttr,
    ExportLayout,
    export_column_name,
)
from medlogserver.worker.tasks.export_study_data import ExportContainer

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
TABLE_SCHEMA_PROFILE = "https://datapackage.org/profiles/2.0/tableschema.json"

# Reference list values per drug attribute name, as (code, display) pairs. Only for
# attributes whose list is small (`is_large_reference_list == False`).
ReferenceValues = Dict[str, List[Tuple[str, str]]]


@dataclass
class ExportSchemaVersions:
    """What a schema is valid for. Written into the schema and used as storage key."""

    medlog_version: str
    drug_importer: str
    drug_dataset_name: str
    drug_dataset_version: str

    def metadata(self) -> Dict[str, str]:
        return {
            "medlog_version": self.medlog_version,
            "drug_importer": self.drug_importer,
            "drug_dataset_name": self.drug_dataset_name,
            "drug_dataset_version": self.drug_dataset_version,
        }

    def schema_id(self, format_: ExportSchemaFormat) -> str:
        # A URN instead of the download URL: it identifies the version combination
        # and does not depend on the public URL of the installation.
        return (
            f"urn:dzdmedlog:export-schema:{ExportSchemaFormat(format_).value}:"
            f"{self.medlog_version}:{self.drug_dataset_name}:{self.drug_dataset_version}"
        )


# The drug attributes every drug has (`FIXED_DRUG_ATTR_NAMES`), they have no importer
# field definition. Values as written by `drug_to_export_data()`.
FIXED_DRUG_ATTR_DESCRIPTIONS: Dict[str, str] = {
    "trade_name": "Trade name of the drug.",
    "market_access_date": "Date the drug entered the market (`YYYY-MM-DD`). Empty if the date is unknown.",
    "market_exit_date": "Date the drug left the market (`YYYY-MM-DD`). Empty if the drug is still on the market or the date is unknown.",
    "is_custom_drug": "`True` for a custom drug entered by a MedLog user, `False` for a drug from the drug dataset.",
    "custom_drug_notes": "Notes of the user who entered the custom drug.",
}
FIXED_DRUG_ATTR_TABLE_FIELDS: Dict[str, Dict[str, Any]] = {
    "trade_name": {"type": "string"},
    "market_access_date": {"type": "date"},
    "market_exit_date": {"type": "date"},
    "is_custom_drug": {
        "type": "boolean",
        "trueValues": ["True"],
        "falseValues": ["False"],
    },
    "custom_drug_notes": {"type": "string"},
}

MULTI_VALUE_CSV_NOTE = (
    "Multi value attribute: the CSV cell holds a Python list repr, e.g. "
    "`['a', 'b', None]`, so the column can only be typed as string."
)


class ExportJsonSchemaGenerator(GenerateJsonSchema):
    """Marks fields with defaults as required in serialization mode.

    Same as `json_schema_serialization_defaults_required=True` in the model config,
    without changing the config of the API models: the export always writes every
    field, also the ones that have a default.
    """

    # The default of `DrugDataExport.drug_attr_reference_code` is a marker class.
    # That definition is replaced in `build_export_json_schema()` anyway.
    ignored_warning_kinds = {"skipped-choice", "non-serializable-default"}

    def field_is_required(
        self,
        field: (
            core_schema.ModelField
            | core_schema.DataclassField
            | core_schema.TypedDictField
        ),
        total: bool,
    ) -> bool:
        if self.mode == "serialization":
            return field.get("serialization_exclude_if") is None
        return super().field_is_required(field, total)


def _model_serialization_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    return model.model_json_schema(
        mode="serialization", schema_generator=ExportJsonSchemaGenerator
    )


def _value_type_name(attr: ExportDrugAttr) -> Optional[str]:
    if attr.field_definition is None:
        return None
    return ValueTypeCasting(attr.field_definition.value_type).name


def _drug_attr_title(attr: ExportDrugAttr) -> str:
    if attr.field_definition is None:
        return attr.name.replace("_", " ").capitalize()
    return attr.field_definition.field_name_display or attr.name


def _drug_attr_description(attr: ExportDrugAttr) -> str:
    if attr.field_definition is None:
        return FIXED_DRUG_ATTR_DESCRIPTIONS.get(attr.name, "")
    parts = []
    if attr.field_definition.field_desc:
        field_desc = attr.field_definition.field_desc.strip()
        parts.append(field_desc if field_desc.endswith((".", "!", "?")) else f"{field_desc}.")
    value_type = _value_type_name(attr)
    if attr.is_reference:
        parts.append(
            "Reference list attribute: the value is the display text of the "
            f"reference list entry, the reference code is its code (value type {value_type})."
        )
    else:
        parts.append(f"Value type {value_type}, written as string.")
    return " ".join(parts)


#########################
# JSON Schema           #
#########################


def _nullable_strings(allowed: Optional[List[str]]) -> Dict[str, Any]:
    if allowed is None:
        return {"type": ["string", "null"]}
    return {"enum": [*allowed, None]}


def _json_drug_attr_value_schemas(
    attr: ExportDrugAttr, reference_values: ReferenceValues
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Schemas of `drug_attr_value` and `drug_attr_reference_code` (None if not a reference)."""
    displays = codes = None
    if attr.name in reference_values:
        codes = sorted({code for code, _ in reference_values[attr.name]})
        displays = sorted({display for _, display in reference_values[attr.name]})
    value = _nullable_strings(displays if attr.is_reference else None)
    code = _nullable_strings(codes) if attr.is_reference else None
    if attr.is_multi:
        value = {"type": ["array", "null"], "items": value}
        if code is not None:
            code = {"type": ["array", "null"], "items": code}
    return value, code


def _json_drug_attr_rule(
    attr: ExportDrugAttr, reference_values: ReferenceValues
) -> Dict[str, Any]:
    value, code = _json_drug_attr_value_schemas(attr, reference_values)
    value = {
        "title": _drug_attr_title(attr),
        "description": _drug_attr_description(attr),
        **value,
    }
    if _value_type_name(attr):
        value["x-medlog-value-type"] = _value_type_name(attr)
    then: Dict[str, Any] = {"properties": {"drug_attr_value": value}}
    if code is None:
        then["not"] = {"required": ["drug_attr_reference_code"]}
    else:
        then["properties"]["drug_attr_reference_code"] = code
        then["required"] = ["drug_attr_reference_code"]
    return {
        "if": {"properties": {"drug_attr_name": {"const": attr.name}}},
        "then": then,
    }


def build_export_json_schema(
    layout: ExportLayout,
    reference_values: ReferenceValues,
    versions: ExportSchemaVersions,
) -> Dict[str, Any]:
    """JSON Schema of the JSON export (`ExportContainer`)."""
    schema = _model_serialization_schema(ExportContainer)
    defs: Dict[str, Any] = schema["$defs"]

    defs["DrugCodesExport"] = {
        "title": "DrugCodesExport",
        "description": "A code of the drug. Only the codes the drug has are listed.",
        "type": "object",
        "properties": {
            "drug_code_system_name": {
                "description": "Name of the code system.",
                "enum": [code_system.name for code_system in layout.code_systems],
            },
            "drug_code": {"type": "string"},
        },
        "required": ["drug_code_system_name", "drug_code"],
        "additionalProperties": False,
    }
    # Replaces the generated definition: its `drug_attr_reference_code` had a
    # meaningless `{}` branch for the `ValueReferenceCodeNotApplicable` marker, and
    # nothing about the known attributes.
    defs["DrugDataExport"] = {
        "title": "DrugDataExport",
        "description": (
            "One drug attribute. Every intake lists all attributes known to the drug "
            "importer, in a fixed order, with null for missing values. Values are "
            "strings, whatever the value type of the attribute. Reference list "
            "attributes also have `drug_attr_reference_code`, the other attributes "
            "do not have this key."
        ),
        "type": "object",
        "properties": {
            "drug_attr_name": {"enum": [attr.name for attr in layout.drug_attrs]},
            "drug_attr_value": {},
            "drug_attr_reference_code": {},
        },
        "required": ["drug_attr_name", "drug_attr_value"],
        "additionalProperties": False,
        "allOf": [
            _json_drug_attr_rule(attr, reference_values) for attr in layout.drug_attrs
        ],
    }

    schema.pop("title", None)
    return {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": versions.schema_id(ExportSchemaFormat.JSON),
        "title": "DZDMedLog study export (JSON)",
        "description": (
            "Schema of the JSON study export of this DZDMedLog installation. The drug "
            "attributes depend on the drug importer and the imported drug dataset, "
            "see `drug_importer`, `drug_dataset_name` and `drug_dataset_version`. "
            "Allowed reference list values are only listed for small reference lists, "
            "they include the values of all imported versions of the drug dataset."
        ),
        **versions.metadata(),
        **schema,
    }


#########################
# Table Schema (CSV)    #
#########################


def _resolve_ref(prop: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
    if "$ref" in prop:
        resolved = dict(defs[prop["$ref"].split("/")[-1]])
        resolved.update({k: v for k, v in prop.items() if k != "$ref"})
        return resolved
    return prop


def _table_field_from_json_schema(
    name: str, prop: Dict[str, Any], defs: Dict[str, Any], required: bool
) -> Dict[str, Any]:
    """Table Schema field for a property of a fixed export model.

    Written by the CSV export with `str()` of the Python value, see module docstring.
    """
    # The title of a referenced definition is the class name (e.g. of an enum)
    title = prop.get("title")
    prop = _resolve_ref(prop, defs)
    nullable = False
    if "anyOf" in prop:
        branches = [_resolve_ref(b, defs) for b in prop["anyOf"]]
        nullable = any(b.get("type") == "null" for b in branches)
        not_null = [b for b in branches if b.get("type") != "null"]
        if len(not_null) == 1:
            prop = {**not_null[0], **{k: v for k, v in prop.items() if k != "anyOf"}}
    field: Dict[str, Any] = {"name": name, "type": "string"}
    if title:
        field["title"] = title
    if prop.get("description"):
        field["description"] = prop["description"]
    constraints: Dict[str, Any] = {}
    json_type = prop.get("type")
    json_format = prop.get("format")
    if "enum" in prop:
        constraints["enum"] = [value for value in prop["enum"] if value is not None]
    elif json_type == "boolean":
        field.update(type="boolean", trueValues=["True"], falseValues=["False"])
    elif json_type == "integer":
        field["type"] = "integer"
    elif json_type == "number":
        field["type"] = "number"
    elif json_type == "string" and json_format == "date":
        field["type"] = "date"
    elif json_type == "string" and json_format == "date-time":
        # `str(datetime)` gives `YYYY-MM-DD HH:MM:SS[.ffffff]`, not ISO 8601 with `T`
        field.update(type="datetime", format="any")
    elif json_type == "string" and json_format == "uuid":
        field["format"] = "uuid"
    if json_type == "string" and "maxLength" in prop:
        constraints["maxLength"] = prop["maxLength"]
    if required and not nullable:
        constraints["required"] = True
    if constraints:
        field["constraints"] = constraints
    return field


def _table_fixed_fields() -> List[Dict[str, Any]]:
    # Same naming and collision handling as `ExportLayout.fixed_columns()`: the first
    # occurrence of a column name fixes its position. Rows are filled with `update()`
    # in the same order, so the last object writes the value and gets to describe it.
    fields: Dict[str, Dict[str, Any]] = {}
    for obj_name, model in FIXED_EXPORT_OBJECTS:
        schema = _model_serialization_schema(model)
        required = set(schema.get("required", []))
        for prop_name, prop in schema["properties"].items():
            name = export_column_name(obj_name, prop_name)
            fields[name] = _table_field_from_json_schema(
                name, prop, schema.get("$defs", {}), prop_name in required
            )
    return list(fields.values())


_VALUE_TYPE_TABLE_FIELDS: Dict[ValueTypeCasting, Dict[str, Any]] = {
    ValueTypeCasting.STR: {"type": "string"},
    ValueTypeCasting.INT: {"type": "integer"},
    ValueTypeCasting.FLOAT: {"type": "number"},
    # The raw source value is written, which is not necessarily `True`/`False`
    # (the importers only check that `bool()` accepts it, which is always the case).
    ValueTypeCasting.BOOL: {"type": "string"},
    ValueTypeCasting.DATE: {"type": "date"},
    ValueTypeCasting.DATETIME: {"type": "datetime", "format": "any"},
}


def _table_drug_attr_fields(
    attr: ExportDrugAttr, reference_values: ReferenceValues
) -> List[Dict[str, Any]]:
    title = _drug_attr_title(attr)
    description = _drug_attr_description(attr)
    if attr.is_multi:
        description = f"{description} {MULTI_VALUE_CSV_NOTE}"
    value_field: Dict[str, Any] = {
        "name": attr.value_column,
        "title": title,
        "description": description,
    }
    if attr.field_definition is None:
        value_field.update(FIXED_DRUG_ATTR_TABLE_FIELDS.get(attr.name, {"type": "string"}))
    elif attr.is_multi or attr.is_reference:
        # multi values are list reprs, single reference values are display texts
        value_field["type"] = "string"
    else:
        value_field.update(
            _VALUE_TYPE_TABLE_FIELDS[ValueTypeCasting(attr.field_definition.value_type)]
        )
    if not attr.is_reference:
        return [value_field]

    code_field: Dict[str, Any] = {
        "name": attr.reference_code_column,
        "title": f"{title} (code)",
        "description": f"Reference code of `{attr.value_column}`. {description}",
        # codes are identifiers (`0` and `00` differ), so always typed as string
        "type": "string",
    }
    if attr.name in reference_values and not attr.is_multi:
        value_field["constraints"] = {
            "enum": sorted({display for _, display in reference_values[attr.name]})
        }
        code_field["constraints"] = {
            "enum": sorted({code for code, _ in reference_values[attr.name]})
        }
    return [value_field, code_field]


def build_export_table_schema(
    layout: ExportLayout,
    reference_values: ReferenceValues,
    versions: ExportSchemaVersions,
) -> Dict[str, Any]:
    """Frictionless Table Schema of the CSV export.

    The fields are exactly `layout.csv_columns()`, in the same order.
    """
    fields = _table_fixed_fields()
    for code_system, column in zip(layout.code_systems, layout.drug_code_columns()):
        fields.append(
            {
                "name": column,
                "title": code_system.name,
                "description": (
                    f"Code of the drug in the code system `{code_system.name}`"
                    + (f" ({code_system.desc.strip()})" if code_system.desc else "")
                    + ". Empty if the drug has no code in this system."
                ),
                "type": "string",
            }
        )
    for attr in layout.drug_attrs:
        fields.extend(_table_drug_attr_fields(attr, reference_values))

    field_names = [field["name"] for field in fields]
    if field_names != layout.csv_columns():
        # Both are built from the same layout, so this is a bug in this module.
        raise ValueError(
            "Export Table Schema fields do not match the CSV export columns. "
            f"Schema: {field_names}, CSV: {layout.csv_columns()}"
        )
    return {
        "$schema": TABLE_SCHEMA_PROFILE,
        "$id": versions.schema_id(ExportSchemaFormat.CSV),
        "title": "DZDMedLog study export (CSV)",
        "description": (
            "Table Schema of the CSV study export of this DZDMedLog installation. Every "
            "CSV export of the installation has exactly these columns in this order. "
            "Drug columns depend on the drug importer and the imported drug dataset, "
            "see `drug_importer`, `drug_dataset_name` and `drug_dataset_version`. "
            "Allowed reference list values are only listed for small, single value "
            "reference lists, they include the values of all imported versions of the "
            f"drug dataset. {MULTI_VALUE_CSV_NOTE}"
        ),
        **versions.metadata(),
        "fieldsMatch": "exact",
        "missingValues": [""],
        "fields": fields,
    }


def build_export_schemas(
    layout: ExportLayout,
    reference_values: ReferenceValues,
    versions: ExportSchemaVersions,
) -> Dict[ExportSchemaFormat, Dict[str, Any]]:
    return {
        ExportSchemaFormat.JSON: build_export_json_schema(
            layout, reference_values, versions
        ),
        ExportSchemaFormat.CSV: build_export_table_schema(
            layout, reference_values, versions
        ),
    }
