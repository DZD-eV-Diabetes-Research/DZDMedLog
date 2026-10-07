"""The study export has the same columns for every study (issue #387).

The CSV header used to be the union of the columns of the exported rows, so the drug
columns depended on which drugs a study referenced. Now the header comes from
`ExportLayout`, built from the export models and the drug importer field definitions.
"""

import csv
import io
import json
import uuid

from utils import req, dictyfy
from tests_export_performance import (
    session_db,
    _create_custom_drug_with_multi_ref,
    _export_layout,
    _pick_imported_drug_ids,
    _run_export,
    _seed_study,
)

from medlogserver.model.drug_data.drug import DrugCustomCreate
from medlogserver.worker.tasks.export_study_data import StudyDataExporter


def _create_custom_drug_with_trade_name_only(trade_name: str) -> uuid.UUID:
    drug = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(DrugCustomCreate(trade_name=trade_name)),
    )
    return uuid.UUID(drug["id"])


def _export_csv(session_db, tmp_path, study_id: uuid.UUID):
    target = tmp_path / f"{study_id}.csv"
    _run_export(session_db, StudyDataExporter, study_id, "csv", target)
    reader = csv.DictReader(io.StringIO(target.read_text(encoding="utf-8")))
    return reader.fieldnames, list(reader)


def test_csv_export_has_columns_no_drug_has_a_value_for(session_db, tmp_path):
    drug_id = _create_custom_drug_with_trade_name_only(
        "Export stable columns drug without attrs"
    )
    seeded = _seed_study(
        session_db,
        name="Export stable columns no values",
        intake_count=3,
        drug_ids=[drug_id],
    )
    header, rows = _export_csv(session_db, tmp_path, seeded.study_id)
    assert header == _export_layout().csv_columns()
    assert len(rows) == 3
    for column in (
        "drug_attr_value_producing_country",
        "drug_attr_reference_code_producing_country",
        "drug_attr_value_keywords",
    ):
        assert column in header
        assert all(row[column] == "" for row in rows)
    assert all(
        row["drug_attr_value_trade_name"] == "Export stable columns drug without attrs"
        for row in rows
    )


def test_csv_exports_of_studies_with_different_drugs_have_the_same_header(
    session_db, tmp_path
):
    imported_drug_ids = _pick_imported_drug_ids(session_db, minimum=10)
    study_a = _seed_study(
        session_db,
        name="Export stable columns study A",
        intake_count=20,
        drug_ids=imported_drug_ids[:5],
    )
    study_b = _seed_study(
        session_db,
        name="Export stable columns study B",
        intake_count=20,
        drug_ids=[
            _create_custom_drug_with_trade_name_only(
                "Export stable columns drug study B"
            ),
            _create_custom_drug_with_multi_ref(
                "Export stable columns drug with refs study B"
            ),
        ],
    )
    study_empty = _seed_study(
        session_db,
        name="Export stable columns study without intakes",
        intake_count=0,
        drug_ids=imported_drug_ids,
    )
    header_a, rows_a = _export_csv(session_db, tmp_path, study_a.study_id)
    header_b, rows_b = _export_csv(session_db, tmp_path, study_b.study_id)
    header_empty, rows_empty = _export_csv(session_db, tmp_path, study_empty.study_id)
    assert len(rows_a) == len(rows_b) == 20
    assert rows_empty == []
    assert header_a == header_b == header_empty == _export_layout().csv_columns()
    # fixed columns first, drug codes before drug attributes
    assert header_a[0] == "study_display_name"
    first_drug_code = min(
        i for i, c in enumerate(header_a) if c.startswith("drug_code_")
    )
    last_drug_code = max(
        i for i, c in enumerate(header_a) if c.startswith("drug_code_")
    )
    first_drug_attr = min(
        i for i, c in enumerate(header_a) if c.startswith("drug_attr_")
    )
    assert all(not c.startswith("drug_") for c in header_a[:first_drug_code])
    assert last_drug_code < first_drug_attr


def test_json_export_lists_all_drug_attrs(session_db, tmp_path):
    drug_id = _create_custom_drug_with_trade_name_only(
        "Export stable columns drug without attrs json"
    )
    seeded = _seed_study(
        session_db,
        name="Export stable columns json",
        intake_count=2,
        drug_ids=[drug_id],
    )
    target = tmp_path / "export.json"
    _run_export(session_db, StudyDataExporter, seeded.study_id, "json", target)
    export = json.loads(target.read_text(encoding="utf-8"))
    layout = _export_layout()
    for intake in export["intakes"]:
        attrs = {a["drug_attr_name"]: a for a in intake["drug_attrs"]}
        assert list(attrs) == [attr.name for attr in layout.drug_attrs]
        assert attrs["trade_name"]["drug_attr_value"] == (
            "Export stable columns drug without attrs json"
        )
        # reference attributes have a (null) reference code, the others none
        assert attrs["producing_country"] == {
            "drug_attr_name": "producing_country",
            "drug_attr_value": None,
            "drug_attr_reference_code": None,
        }
        assert attrs["keywords"] == {
            "drug_attr_name": "keywords",
            "drug_attr_value": None,
        }
