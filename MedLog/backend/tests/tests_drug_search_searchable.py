"""Tests for the `searchable` flag of drug field definitions and code systems (issue #214).

Only fields and code systems flagged `searchable` may end up in the search index.
That holds for all five kinds (attrs, attrs_multi, attrs_ref, attrs_multi_ref and
codes) and for both ways a drug gets indexed: the bulk index build in SQL and the
single drug insert used for custom drugs.

Code systems had no such flag before, every code was indexed. The MMI Pharmindex
search must not change in a way users notice, which `test_mmi_pharmindex_search_fields_unchanged`
pins down.

The index tests run against their own throwaway SQLite database, see
`tests_drug_market_accessability.py` for the fixture.
"""

from typing import Dict, List
import asyncio
import datetime
import importlib.util
from pathlib import Path
import uuid

import sqlalchemy as sa
from sqlmodel import select

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (registers metadata)
from medlogserver.db.drug_data.drug_search import GenericSQLDrugSearchCache
from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
    GenericSQLDrugSearchEngine,
)
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValMulti,
    DrugValMultiRef,
    DrugValRef,
)
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.config import Config

# the shared throwaway database fixture
from tests_drug_market_accessability import isolated_db  # noqa: F401

config = Config()
IMPORTER = config.DRUG_IMPORTER_PLUGIN
DATASET_SOURCE_NAME = DRUG_IMPORTERS[IMPORTER]().dataset_name
BACKEND_DIR = Path(__file__).resolve().parent.parent

TRADE_NAME = "Suchbarkeitstest"

# kind -> (searchable field, not searchable field). Every value and LOV display
# is a unique token, so its presence in the index tells exactly where it came from.
FIELDS = {
    "attrs": ("s_attr", "n_attr"),
    "attrs_multi": ("s_multi", "n_multi"),
    "attrs_ref": ("s_ref", "n_ref"),
    "attrs_multi_ref": ("s_mref", "n_mref"),
}
CODE_SYSTEMS = ("SCODE", "NCODE")


def _value(field_name: str) -> str:
    return f"val{field_name.replace('_', '')}"


def _display(field_name: str) -> str:
    return f"disp{field_name.replace('_', '')}"


def _code(code_system_id: str) -> str:
    return f"code{code_system_id.lower()}"


SEARCHABLE_TOKENS = (
    [_value(s) for s, _ in FIELDS.values()]
    + [_display(FIELDS["attrs_ref"][0]), _display(FIELDS["attrs_multi_ref"][0])]
    + [_code(CODE_SYSTEMS[0])]
)
NOT_SEARCHABLE_TOKENS = (
    [_value(n) for _, n in FIELDS.values()]
    + [_display(FIELDS["attrs_ref"][1]), _display(FIELDS["attrs_multi_ref"][1])]
    + [_code(CODE_SYSTEMS[1])]
)


def _definitions() -> Dict[str, List]:
    defs: Dict[str, List] = {}
    for kind, names in FIELDS.items():
        defs[kind] = [
            DrugAttrFieldDefinition(
                field_name=name,
                field_name_display=name,
                importer_name=IMPORTER,
                is_reference_list_field=kind in ("attrs_ref", "attrs_multi_ref"),
                is_multi_val_field=kind in ("attrs_multi", "attrs_multi_ref"),
                searchable=name == names[0],
            )
            for name in names
        ]
    defs["codes"] = [
        DrugCodeSystem(
            id=code_system_id,
            name=code_system_id,
            country="Nowhere",
            importer_name=IMPORTER,
            searchable=code_system_id == CODE_SYSTEMS[0],
        )
        for code_system_id in CODE_SYSTEMS
    ]
    return defs


def _search_engine() -> GenericSQLDrugSearchEngine:
    engine = GenericSQLDrugSearchEngine()
    engine._all_drug_attr_field_definitions = _definitions()
    engine._market_accessability_definition = None
    return engine


async def _seed(session) -> uuid.UUID:
    active = DrugDataSetVersion(
        id=uuid.uuid4(),
        dataset_version="v_searchable_test",
        dataset_source_name=DATASET_SOURCE_NAME,
        is_custom_drugs_collection=False,
        current_active=True,
        import_status="done",
        import_start_datetime_utc=datetime.datetime.now(datetime.UTC),
    )
    custom = DrugDataSetVersion(
        id=uuid.uuid4(),
        dataset_version="custom",
        dataset_source_name=DATASET_SOURCE_NAME,
        is_custom_drugs_collection=True,
        current_active=False,
        import_status="done",
        import_start_datetime_utc=datetime.datetime.now(datetime.UTC),
    )
    session.add_all([active, custom])
    await session.commit()

    defs = _definitions()
    for kind in FIELDS:
        session.add_all(defs[kind])
    session.add_all(defs["codes"])
    await session.commit()

    for name in FIELDS["attrs_ref"] + FIELDS["attrs_multi_ref"]:
        session.add(
            DrugAttrFieldLovItem(
                field_name=name,
                importer_name=IMPORTER,
                value=_value(name),
                display=_display(name),
                drug_dataset_version_fk=active.id,
            )
        )
    await session.commit()

    drug = DrugData(
        id=uuid.uuid4(),
        source_dataset_id=active.id,
        trade_name=TRADE_NAME,
        is_custom_drug=False,
        custom_drug_notes=None,
    )
    session.add(drug)
    await session.commit()

    common = dict(
        drug_id=drug.id, importer_name=IMPORTER, drug_dataset_version_fk=active.id
    )
    for name in FIELDS["attrs"]:
        session.add(DrugVal(field_name=name, value=_value(name), **common))
    for name in FIELDS["attrs_multi"]:
        session.add(
            DrugValMulti(field_name=name, value=_value(name), value_index=0, **common)
        )
    for name in FIELDS["attrs_ref"]:
        session.add(DrugValRef(field_name=name, value=_value(name), **common))
    for name in FIELDS["attrs_multi_ref"]:
        session.add(
            DrugValMultiRef(
                field_name=name, value=_value(name), value_index=0, **common
            )
        )
    for code_system_id in CODE_SYSTEMS:
        session.add(
            DrugCode(
                code_system_id=code_system_id, code=_code(code_system_id), **common
            )
        )
    await session.commit()
    return drug.id


def _assert_only_searchable_indexed(cache: GenericSQLDrugSearchCache):
    content = cache.search_index_content
    assert content.startswith(TRADE_NAME)
    for token in SEARCHABLE_TOKENS:
        assert token in content, f"'{token}' missing in index: {content}"
    for token in NOT_SEARCHABLE_TOKENS:
        assert token not in content, f"'{token}' must not be indexed: {content}"
    assert cache.search_cache_codes == f"{CODE_SYSTEMS[0]}:{_code(CODE_SYSTEMS[0])}"


def test_index_build_honors_searchable_issue_214(isolated_db):
    """The bulk index build only aggregates searchable fields and codes."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context

        async with get_async_session_context() as session:
            drug_id = await _seed(session)

        await _search_engine().build_index(force_rebuild=True)

        async with get_async_session_context() as session:
            cache = (
                await session.exec(
                    select(GenericSQLDrugSearchCache).where(
                        GenericSQLDrugSearchCache.id == drug_id
                    )
                )
            ).one()
        _assert_only_searchable_indexed(cache)

    asyncio.run(scenario())


def test_single_drug_index_honors_searchable_issue_214(isolated_db):
    """The single drug insert (custom drugs) indexes the same as the bulk build."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context

        async with get_async_session_context() as session:
            drug_id = await _seed(session)

        async with get_async_session_context() as session:
            drug = (
                await session.exec(select(DrugData).where(DrugData.id == drug_id))
            ).one()
            cache = await _search_engine()._drug_to_cache_obj(drug)
        _assert_only_searchable_indexed(cache)

    asyncio.run(scenario())


def test_single_drug_index_multi_ref_without_lov_item(isolated_db):
    """A multi ref value without LOV item used to crash the single drug insert."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context

        async with get_async_session_context() as session:
            drug_id = await _seed(session)
            await session.exec(
                sa.delete(DrugAttrFieldLovItem).where(
                    DrugAttrFieldLovItem.field_name == FIELDS["attrs_multi_ref"][0]
                )
            )
            await session.commit()

        async with get_async_session_context() as session:
            drug = (
                await session.exec(select(DrugData).where(DrugData.id == drug_id))
            ).one()
            cache = await _search_engine()._drug_to_cache_obj(drug)
        # the value is still indexed, just without a display text
        assert _value(FIELDS["attrs_multi_ref"][0]) in cache.search_index_content
        assert _display(FIELDS["attrs_multi_ref"][0]) not in cache.search_index_content

    asyncio.run(scenario())


def test_mmi_pharmindex_search_fields_unchanged():
    """MMI Pharmindex users are happy with the drug search as it is.

    This is what the index contained before issue #214, minus the internal MMIP
    product ID. MMIP is not shown in the UI, and on a 5000 drug MMI dataset leaving it
    out kept the top hit of every trade name, PZN and ATC query. It only dropped noise
    hits of number queries. Changing this changes what users find, so do it on
    purpose only.
    """
    from medlogserver.db.drug_data.importers.mmi_pharmindex import (
        MMIPharmindex1_32,
    )

    defs = asyncio.run(MMIPharmindex1_32().get_all_attr_field_definitions())
    searchable = {
        kind: sorted(
            d.id if kind == "codes" else d.field_name
            for d in field_defs
            if d.searchable
        )
        for kind, field_defs in defs.items()
    }
    assert searchable == {
        "codes": ["PZN"],
        "attrs": [],
        "attrs_multi": ["ATC"],
        "attrs_ref": ["darreichungsform"],
        "attrs_multi_ref": ["applikationsart", "icd10", "keywords"],
    }


def test_build_index_sql_without_searchable_codes():
    """No searchable code system means no code aggregation at all."""
    for is_pg in (False, True):
        sql = GenericSQLDrugSearchEngine()._build_index_insert_sql(
            searchable_attrs=[],
            searchable_multi=[],
            searchable_ref=[],
            searchable_multi_ref=[],
            searchable_codes=[],
            is_pg=is_pg,
        )
        assert "drug_code" not in sql
        assert "ac." not in sql


# ─────────────────────────── migration d0e1f2a3b4c5 ─────────────────────────


def _run_migration(func_name: str, connection):
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations

    mig_path = (
        BACKEND_DIR
        / "medlogserver/db_migrations/versions/"
        "d0e1f2a3b4c5_add_searchable_to_drug_code_system.py"
    )
    spec = importlib.util.spec_from_file_location("mig_d0e1f2a3b4c5", mig_path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    mig.op = Operations(MigrationContext.configure(connection))
    getattr(mig, func_name)()


def test_migration_marks_existing_code_systems_searchable(tmp_path):
    """Existing code systems were all indexed so far, they stay searchable."""
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'mig_searchable.db'}")
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE drug_code_system (id VARCHAR PRIMARY KEY, name VARCHAR)"
            )
        )
        conn.execute(sa.text("INSERT INTO drug_code_system VALUES ('PZN', 'P')"))
    with engine.begin() as conn:
        _run_migration("upgrade", conn)
    with engine.connect() as conn:
        assert (
            conn.execute(sa.text("SELECT searchable FROM drug_code_system")).scalar()
            == 1
        )
    with engine.begin() as conn:
        _run_migration("downgrade", conn)
    with engine.connect() as conn:
        cols = [
            r[1] for r in conn.execute(sa.text("PRAGMA table_info(drug_code_system)"))
        ]
        assert "searchable" not in cols
