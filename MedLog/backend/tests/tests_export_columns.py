"""Export column changes of issue #389.

The test database only has the dummy drug dataset, so the MMI Pharmindex specific
parts are tested with a drug object built by hand and the export layout of the MMI
importer (its field definitions are defined in code, no drug data needed).
"""

import asyncio
import datetime
import json
import uuid
from types import SimpleNamespace

from medlogserver.model.intake import (
    ConsumedMedsTodayAnswers,
    IntakeExport,
    IntakeRegularOrAsNeededAnswers,
    IntervalOfDailyDoseAnswers,
)
from medlogserver.model.study import StudyExport
from medlogserver.db.drug_data.importers.mmi_pharmindex import (
    MMIPharmindex1_32,
    importername as MMI,
)
from medlogserver.worker.tasks.export_layout import (
    ExportLayout,
    flatten_export_drug_codes,
    flatten_export_objects,
)
from medlogserver.worker.tasks.export_study_data import drug_to_export_data


def _mmi_drug():
    def attr(field_name, value):
        return SimpleNamespace(importer_name=MMI, field_name=field_name, value=value)

    def ref(field_name, value, display):
        return SimpleNamespace(
            importer_name=MMI,
            field_name=field_name,
            value=value,
            lov_item=SimpleNamespace(display=display),
        )

    def code(code_system_id, name, value):
        return SimpleNamespace(
            code=value, code_system=SimpleNamespace(id=code_system_id, name=name)
        )

    return SimpleNamespace(
        trade_name="Aspirin Direkt 500 mg",
        market_access_date=datetime.date(1993, 1, 2),
        market_exit_date=None,
        is_custom_drug=False,
        custom_drug_notes=None,
        codes=[
            code("PZN", "Pharmazentralnummer", "04356248"),
            code("MMIP", "MMI Product ID", "113746"),
        ],
        attrs=[
            attr("amount", "10 st"),
            attr("ist_generikum", "1"),
            attr("ist_kosmetikum", "0"),
            attr("ist_pflanzlich", None),
        ],
        attrs_ref=[
            ref("lebensmittel", "N", "Nein"),
            ref("diaetetikum", "E", "Sonstige Diätetikum"),
            ref("hersteller", "10245", "Bayer Vital GmbH"),
        ],
        attrs_multi=[],
        attrs_multi_ref=[],
    )


MMI_LAYOUT = asyncio.run(ExportLayout.from_importer(MMIPharmindex1_32()))


def _drug_columns():
    codes, attrs = drug_to_export_data(_mmi_drug(), MMI_LAYOUT)
    columns = flatten_export_drug_codes(codes)
    columns.update(flatten_export_objects(attrs, "drug", "drug_attr_name"))
    return columns


def test_drug_code_columns_named_by_code_system_id():
    columns = _drug_columns()
    assert columns["drug_code_pzn"] == "04356248"
    assert columns["drug_code_mmip"] == "113746"
    assert not [c for c in columns if " " in c], columns.keys()
    assert not [c for c in columns if "system_name" in c], columns.keys()


def test_empty_market_date_is_not_the_text_none():
    columns = _drug_columns()
    assert columns["drug_attr_value_market_access_date"] == "1993-01-02"
    assert columns["drug_attr_value_market_exit_date"] is None


def test_booleans_are_normalized():
    columns = _drug_columns()
    assert columns["drug_attr_value_ist_generikum"] is True
    assert columns["drug_attr_value_ist_kosmetikum"] is False
    assert columns["drug_attr_value_ist_pflanzlich"] is None
    assert columns["drug_attr_value_is_custom_drug"] is False
    # not a BOOL field, stays untouched
    assert columns["drug_attr_value_amount"] == "10 st"


def test_redundant_mmi_reference_codes_are_removed():
    columns = _drug_columns()
    # three valued (Ja, Nein, Sonstige), so the display text stays
    assert columns["drug_attr_value_lebensmittel"] == "Nein"
    assert columns["drug_attr_value_diaetetikum"] == "Sonstige Diätetikum"
    assert "drug_attr_reference_code_lebensmittel" not in columns
    assert "drug_attr_reference_code_diaetetikum" not in columns
    # other reference codes stay
    assert columns["drug_attr_reference_code_hersteller"] == "10245"

    _, attrs = drug_to_export_data(_mmi_drug(), MMI_LAYOUT)
    json_attrs = {
        a["drug_attr_name"]: a
        for a in (json.loads(attr.model_dump_json()) for attr in attrs)
    }
    assert json_attrs["lebensmittel"] == {
        "drug_attr_name": "lebensmittel",
        "drug_attr_value": "Nein",
    }
    assert json_attrs["ist_generikum"]["drug_attr_value"] is True


def test_mmi_layout_has_the_issue_389_columns():
    """The CSV header and the export schemas are built from the layout (#387)."""
    columns = MMI_LAYOUT.csv_columns()
    assert "drug_code_pzn" in columns
    assert "drug_code_mmip" in columns
    assert not [c for c in columns if " " in c]
    assert "drug_attr_value_lebensmittel" in columns
    assert "drug_attr_reference_code_lebensmittel" not in columns
    assert "drug_attr_reference_code_diaetetikum" not in columns
    assert "drug_attr_reference_code_hersteller" in columns
    assert "intake_regular_interval_of_daily_dose" in columns
    assert "study_proband_external_id_example" not in columns
    assert MMI_LAYOUT.drug_attrs_by_name["ist_generikum"].is_bool
    assert MMI_LAYOUT.drug_attrs_by_name["is_custom_drug"].is_bool
    assert not MMI_LAYOUT.drug_attrs_by_name["lebensmittel"].is_bool


def test_study_export_without_proband_id_input_helpers():
    study = StudyExport(
        id=uuid.uuid4(),
        display_name="Study",
        created_at=datetime.datetime.now(),
        deactivated=False,
        no_permissions=False,
        proband_external_id_pattern="^[A-Z]{3}[0-9]{4}$",
        proband_external_id_pattern_error_text="3 letters, 4 digits",
        proband_external_id_normalization="uppercase",
        proband_external_id_example="AAA1111",
    )
    assert set(flatten_export_objects(study, "study")) == {
        "study_display_name",
        "study_proband_external_id_pattern",
        "study_id",
    }


def test_intake_export_interval_column_spelled_correctly():
    intake = IntakeExport(
        id=uuid.uuid4(),
        interview_id=uuid.uuid4(),
        created_at=datetime.datetime.now(),
        drug_id=uuid.uuid4(),
        intake_regular_or_as_needed=IntakeRegularOrAsNeededAnswers.REGULAR,
        dose_per_day=1,
        regular_intervall_of_daily_dose=IntervalOfDailyDoseAnswers.DAILY,
        consumed_meds_today=ConsumedMedsTodayAnswers.YES,
    )
    columns = flatten_export_objects(intake, "intake")
    assert "intake_regular_interval_of_daily_dose" in columns
    assert "intake_regular_intervall_of_daily_dose" not in columns
    assert "regular_interval_of_daily_dose" in json.loads(intake.model_dump_json())
