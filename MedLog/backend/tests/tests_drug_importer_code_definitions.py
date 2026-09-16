"""Tests for `get_code_definitions(by_id=...)` of the drug importers.

A code system is identified by `DrugCodeSystem.id` (e.g. "PZN"). The MMI
Pharmindex importer filtered on a non-existent `field_name` attribute (raised
AttributeError) and the dummy importer on the long `name` (never matched).

No database needed, all importers define their code systems in code.
"""

import asyncio

import pytest

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (avoids a circular import when run alone)
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS


@pytest.mark.parametrize("importer_name", sorted(DRUG_IMPORTERS.keys()))
def test_get_code_definitions_by_id(importer_name: str):
    importer = DRUG_IMPORTERS[importer_name]()
    all_code_systems = asyncio.run(importer.get_code_definitions())
    assert any(code_system.id == "PZN" for code_system in all_code_systems)

    by_id = asyncio.run(importer.get_code_definitions(by_id="PZN"))
    assert [code_system.id for code_system in by_id] == ["PZN"]

    assert asyncio.run(importer.get_code_definitions(by_id="DOES-NOT-EXIST")) == []
