"""Tests for syncing the drug field and code definitions from code into the database (issue #218).

The definitions are defined in code. They used to be written only during a drug
dataset import, so the database kept outdated values (e.g. `code_icon`, which the
client reads via `/drug/code_def`) until the next dataset version came in. Now
`init_db()` syncs them on every startup.

Values reset to their default in code must be synced as well, the update must not
only copy fields explicitly set in code.

Runs against its own throwaway SQLite database, see `tests_drug_market_accessability.py`
for the fixture.
"""

from typing import Dict, List
import asyncio

from sqlmodel import select

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (registers metadata)
from medlogserver.db._session import get_async_session_context
from medlogserver.db._init_db import sync_drug_field_definitions
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.config import Config

# the shared throwaway database fixture
from tests_drug_market_accessability import isolated_db  # noqa: F401

config = Config()


def _definitions_in_code() -> Dict[str, List[DrugAttrFieldDefinition | DrugCodeSystem]]:
    importer = DRUG_IMPORTERS[config.DRUG_IMPORTER_PLUGIN]()
    all_defs = asyncio.run(importer.get_all_attr_field_definitions())
    return {
        "codes": all_defs["codes"],
        "attrs": [
            d
            for kind in ("attrs", "attrs_ref", "attrs_multi", "attrs_multi_ref")
            for d in all_defs[kind]
        ],
    }


async def _definitions_in_db():
    async with get_async_session_context() as session:
        codes = (await session.exec(select(DrugCodeSystem))).all()
        attrs = (await session.exec(select(DrugAttrFieldDefinition))).all()
    return {c.id: c for c in codes}, {a.field_name: a for a in attrs}


def _assert_db_matches_code():
    code_defs = _definitions_in_code()
    db_codes, db_attrs = asyncio.run(_definitions_in_db())
    assert set(db_codes) == {c.id for c in code_defs["codes"]}
    assert set(db_attrs) == {a.field_name for a in code_defs["attrs"]}
    for code_def in code_defs["codes"]:
        assert db_codes[code_def.id].model_dump() == code_def.model_dump()
    for attr_def in code_defs["attrs"]:
        assert db_attrs[attr_def.field_name].model_dump() == attr_def.model_dump()


async def _tamper(code_id: str, field_name: str):
    """Simulate outdated rows, as left behind by an older MedLog version."""
    async with get_async_session_context() as session:
        code = (
            await session.exec(select(DrugCodeSystem).where(DrugCodeSystem.id == code_id))
        ).one()
        code.desc = "outdated desc"
        code.code_icon = "outdated icon"
        code.code_display_sort_order = 999
        code.client_visible = not code.client_visible
        session.add(code)

        attr = (
            await session.exec(
                select(DrugAttrFieldDefinition).where(
                    DrugAttrFieldDefinition.field_name == field_name
                )
            )
        ).one()
        attr.field_name_display = "outdated name"
        attr.field_desc = "outdated desc"
        attr.field_icon = "outdated icon"
        attr.field_display_sort_order = 999
        attr.is_large_reference_list = not attr.is_large_reference_list
        attr.show_in_search_results = not attr.show_in_search_results
        attr.used_for_custom_drug = not attr.used_for_custom_drug
        session.add(attr)
        await session.commit()


def test_sync_on_empty_database_inserts_all_definitions(isolated_db):
    asyncio.run(sync_drug_field_definitions())
    _assert_db_matches_code()


def test_sync_is_repeatable(isolated_db):
    asyncio.run(sync_drug_field_definitions())
    asyncio.run(sync_drug_field_definitions())
    _assert_db_matches_code()


def test_sync_overwrites_outdated_values(isolated_db):
    asyncio.run(sync_drug_field_definitions())
    code_defs = _definitions_in_code()
    code_id = code_defs["codes"][0].id
    field_name = code_defs["attrs"][0].field_name
    asyncio.run(_tamper(code_id, field_name))

    db_codes, db_attrs = asyncio.run(_definitions_in_db())
    assert db_codes[code_id].code_icon == "outdated icon"
    assert db_attrs[field_name].field_icon == "outdated icon"

    asyncio.run(sync_drug_field_definitions())
    _assert_db_matches_code()


def test_sync_resets_values_left_on_default_in_code(isolated_db):
    """A field that falls back to its default in code (not explicitly set) is synced too."""
    code_defs = _definitions_in_code()
    code_def = next(
        (c for c in code_defs["codes"] if "code_icon" not in c.model_fields_set), None
    )
    attr_def = next(
        (
            a
            for a in code_defs["attrs"]
            if "show_in_search_results" not in a.model_fields_set
        ),
        None,
    )
    assert code_def is not None and code_def.code_icon is None
    assert attr_def is not None and attr_def.show_in_search_results is True

    asyncio.run(sync_drug_field_definitions())
    asyncio.run(_tamper(code_def.id, attr_def.field_name))
    db_codes, db_attrs = asyncio.run(_definitions_in_db())
    assert db_codes[code_def.id].code_icon == "outdated icon"
    assert db_attrs[attr_def.field_name].show_in_search_results is False

    asyncio.run(sync_drug_field_definitions())

    db_codes, db_attrs = asyncio.run(_definitions_in_db())
    assert db_codes[code_def.id].code_icon is None
    assert db_attrs[attr_def.field_name].show_in_search_results is True
    _assert_db_matches_code()
