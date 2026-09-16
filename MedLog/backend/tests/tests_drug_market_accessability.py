"""Regression tests for the market availability filter (issue #360).

`market_exit_date` cannot answer "is this drug still obtainable" for every drug
data source. MMI Pharmindex keeps packages the supplier stopped delivering in
its live catalog, with no OFFMARKETDATE, and marks them only through the
`vertriebsstatus` attribute (catalog 116: N=Im Vertrieb, F=Außer Vertrieb).
Filtering on the date alone therefore let every "Außer Vertrieb" package pass as
still on the market, which is what the issue reported.

Importers now declare that attribute via `MarketAccessabilityDefinition`, the
index build resolves it into `drug_search_generic_sql_cache.market_accessable`,
and the search filter reads both signals. These tests cover the four states that
combination can produce, plus the "yes" and "no" answers being complements of
each other.

They run against their own throwaway SQLite database rather than the session
database, so they neither depend on nor disturb the live server the other tests
share.
"""

from typing import Dict, List, Optional
import asyncio
import datetime
import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (registers metadata)
from medlogserver.db.drug_data.drug_search import GenericSQLDrugSearchCache
from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
    GenericSQLDrugSearchEngine,
)
from medlogserver.db.drug_data.importers._base import MarketAccessabilityDefinition
from medlogserver.model.drug_data import DrugData, DrugDataSetVersion
from medlogserver.model.drug_data.drug_attr import DrugValRef
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
from medlogserver.model.drug_data.drug_attr import DrugVal
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.db.drug_data.importers import DRUG_IMPORTERS
from medlogserver.config import Config

config = Config()
# The dataset version lookups match on the configured importer's dataset name, so
# the seed has to speak whatever importer this test run is configured with.
IMPORTER = config.DRUG_IMPORTER_PLUGIN
DATASET_SOURCE_NAME = DRUG_IMPORTERS[IMPORTER]().dataset_name
MARKET_FIELD = "vertriebsstatus"
# what MMI catalog 116 means, shortened to the codes this test needs
ON_MARKET = "N"
OFF_MARKET = "F"

# every drug carries this token so a single search term matches all of them
SEARCH_TOKEN = "Marktpruefung"

TODAY = datetime.date.today()

# name -> (sales status, market exit date)
DRUGS: Dict[str, tuple] = {
    # plain "still sold": what the filter always got right
    "on_market": (ON_MARKET, None),
    # issue #360: no exit date, yet not obtainable. Used to pass as on-market.
    "off_market_no_exit_date": (OFF_MARKET, None),
    # archived: both signals agree it is gone
    "off_market_with_exit_date": (OFF_MARKET, TODAY - datetime.timedelta(days=30)),
    # no status at all (custom drugs, importers without the attribute)
    "no_status": (None, None),
    # status says sold, but it leaves the market in the future
    "on_market_future_exit_date": (ON_MARKET, TODAY + datetime.timedelta(days=30)),
    # exit date is exactly today, which is not "still on the market"
    "on_market_exit_date_today": (ON_MARKET, TODAY),
}

# Attributes the configured importer marks as mandatory on its drug API model.
MANDATORY_ATTRS = {"amount": "1", "manufacturer": "Testhersteller"}
MANDATORY_REF_ATTRS = {"dispensingtype": "0"}

ACCESSABLE = {"on_market", "no_status", "on_market_future_exit_date"}
NOT_ACCESSABLE = set(DRUGS) - ACCESSABLE


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """An empty MedLog schema in a throwaway SQLite file, wired into the db layer.

    `medlogserver.db._session` caches its engine in module globals, so pointing the
    search engine at another database means replacing those. monkeypatch restores
    them when the test ends.
    """
    db_file = tmp_path / "market_accessability_test.sqlite"

    SQLModel.metadata.create_all(create_engine(f"sqlite:///{db_file}"))

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        future=True,
        # every test drives its own asyncio.run(), so pooled connections must not
        # outlive the loop that opened them
        poolclass=NullPool,
    )

    from medlogserver.db import _session
    from medlogserver.db.drug_data.drug_search import search_module_generic_sql

    # The index build picks its SQL dialect from the configured database URL. The
    # test session may run against postgres, so point it at the throwaway file the
    # search engine actually talks to.
    monkeypatch.setattr(
        search_module_generic_sql.config,
        "SQL_DATABASE_URL",
        f"sqlite+aiosqlite:///{db_file}",
    )

    monkeypatch.setattr(_session, "_db_engine", engine)
    monkeypatch.setattr(
        _session,
        "_async_session_factory",
        sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        ),
    )
    # _get_engine()/_get_session_factory() rebuild their globals whenever
    # _engine_pid does not match the current process. Pinning it to this process
    # is what keeps them from throwing our objects away and reconnecting to the
    # session database named in the config.
    monkeypatch.setattr(_session, "_engine_pid", os.getpid())

    yield engine

    asyncio.run(engine.dispose())


def _search_engine() -> GenericSQLDrugSearchEngine:
    """A search engine whose importer declares a market status attribute.

    The configured test importer (the dummy one) has no such attribute, so the
    declaration is injected the same way a real importer makes it.
    """
    engine = GenericSQLDrugSearchEngine()
    engine._market_accessability_definition = MarketAccessabilityDefinition(
        field_name=MARKET_FIELD,
        accessable_values=[ON_MARKET],
    )
    return engine


async def _seed(session) -> Dict[str, uuid.UUID]:
    """Create one dataset version plus the drugs from DRUGS, keyed by name."""
    active = DrugDataSetVersion(
        id=uuid.uuid4(),
        dataset_version="v_market_test",
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

    session.add(
        DrugAttrFieldDefinition(
            field_name=MARKET_FIELD,
            field_name_display="Vertriebsstatus",
            importer_name=IMPORTER,
            is_reference_list_field=True,
            is_multi_val_field=False,
            # the real MMI field is not searchable either; the market filter must
            # work regardless of whether the attribute feeds the search index
            searchable=False,
        )
    )
    await session.commit()

    for value, display in ((ON_MARKET, "Im Vertrieb"), (OFF_MARKET, "Außer Vertrieb")):
        session.add(
            DrugAttrFieldLovItem(
                field_name=MARKET_FIELD,
                importer_name=IMPORTER,
                value=value,
                display=display,
                drug_dataset_version_fk=active.id,
            )
        )
    await session.commit()

    for field_name, value in MANDATORY_REF_ATTRS.items():
        session.add(
            DrugAttrFieldLovItem(
                field_name=field_name,
                importer_name=IMPORTER,
                value=value,
                display=f"{field_name} {value}",
                drug_dataset_version_fk=active.id,
            )
        )
    await session.commit()

    drug_ids: Dict[str, uuid.UUID] = {}
    for name, (status, exit_date) in DRUGS.items():
        drug = DrugData(
            id=uuid.uuid4(),
            source_dataset_id=active.id,
            trade_name=f"{SEARCH_TOKEN} {name}",
            market_exit_date=exit_date,
            is_custom_drug=False,
            custom_drug_notes=None,
        )
        session.add(drug)
        drug_ids[name] = drug.id
    await session.commit()

    # `search()` renders its hits through the importer's drug API model, which
    # rejects drugs missing a mandatory attribute. None of them take part in the
    # market filter; they are here so the search results can be built at all.
    session.add(
        DrugCodeSystem(
            id="PZN",
            name="Pharmazentralnummer",
            country="Germany",
            importer_name=IMPORTER,
        )
    )
    await session.commit()
    for position, (name, drug_id) in enumerate(drug_ids.items()):
        session.add(
            DrugCode(
                drug_id=drug_id,
                code_system_id="PZN",
                code=f"1000000{position}",
                importer_name=IMPORTER,
                drug_dataset_version_fk=active.id,
            )
        )
        for field_name, value in MANDATORY_ATTRS.items():
            session.add(
                DrugVal(
                    drug_id=drug_id,
                    field_name=field_name,
                    value=value,
                    importer_name=IMPORTER,
                    drug_dataset_version_fk=active.id,
                )
            )
        for field_name, value in MANDATORY_REF_ATTRS.items():
            session.add(
                DrugValRef(
                    drug_id=drug_id,
                    field_name=field_name,
                    value=value,
                    importer_name=IMPORTER,
                    drug_dataset_version_fk=active.id,
                )
            )
    await session.commit()

    for name, (status, _) in DRUGS.items():
        if status is None:
            continue
        session.add(
            DrugValRef(
                drug_id=drug_ids[name],
                field_name=MARKET_FIELD,
                value=status,
                importer_name=IMPORTER,
                drug_dataset_version_fk=active.id,
            )
        )
    await session.commit()

    return drug_ids


async def _cached_market_accessable(session) -> Dict[uuid.UUID, Optional[bool]]:
    rows = await session.exec(
        select(
            GenericSQLDrugSearchCache.id,
            GenericSQLDrugSearchCache.market_accessable,
        )
    )
    return {row[0]: row[1] for row in rows.all()}


def test_index_resolves_market_status_into_cache(isolated_db):
    """The index build turns the status attribute into a boolean column."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context

        async with get_async_session_context() as session:
            drug_ids = await _seed(session)

        await _search_engine().build_index(force_rebuild=True)

        async with get_async_session_context() as session:
            cached = await _cached_market_accessable(session)

        assert cached[drug_ids["on_market"]] is True
        assert cached[drug_ids["off_market_no_exit_date"]] is False
        assert cached[drug_ids["off_market_with_exit_date"]] is False
        # no status value means "the importer cannot tell", not "unavailable"
        assert cached[drug_ids["no_status"]] is None

    asyncio.run(scenario())


def _names_from(search_result, drug_ids: Dict[str, uuid.UUID]) -> set:
    by_id = {drug_id: name for name, drug_id in drug_ids.items()}
    return {by_id[item.drug_id] for item in search_result.items}


def test_search_filters_by_market_status_issue_360(isolated_db):
    """"Außer Vertrieb" without an exit date must not count as on the market."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context
        from medlogserver.api.paginator import create_query_params_class

        async with get_async_session_context() as session:
            drug_ids = await _seed(session)

        engine = _search_engine()
        await engine.build_index(force_rebuild=True)

        pagination = create_query_params_class(DrugData)()

        accessable = await engine.search(
            search_term=SEARCH_TOKEN, market_accessable=True, pagination=pagination
        )
        not_accessable = await engine.search(
            search_term=SEARCH_TOKEN, market_accessable=False, pagination=pagination
        )
        unfiltered = await engine.search(
            search_term=SEARCH_TOKEN, market_accessable=None, pagination=pagination
        )

        assert _names_from(accessable, drug_ids) == ACCESSABLE
        assert _names_from(not_accessable, drug_ids) == NOT_ACCESSABLE
        # the two answers together must account for every drug, no gap in between
        assert _names_from(unfiltered, drug_ids) == set(DRUGS)

    asyncio.run(scenario())


def test_market_filter_unchanged_without_importer_declaration(isolated_db):
    """An importer without a market status attribute keeps the old behaviour."""

    async def scenario():
        from medlogserver.db._session import get_async_session_context
        from medlogserver.api.paginator import create_query_params_class

        async with get_async_session_context() as session:
            drug_ids = await _seed(session)

        engine = GenericSQLDrugSearchEngine()
        # what a plain importer reports: no market status attribute at all
        engine._market_accessability_definition = None
        await engine.build_index(force_rebuild=True)

        async with get_async_session_context() as session:
            cached = await _cached_market_accessable(session)
        assert set(cached.values()) == {None}

        pagination = create_query_params_class(DrugData)()
        accessable = await engine.search(
            search_term=SEARCH_TOKEN, market_accessable=True, pagination=pagination
        )
        # only the exit date decides now, so the "Außer Vertrieb" drug is back in
        assert _names_from(accessable, drug_ids) == {
            "on_market",
            "off_market_no_exit_date",
            "no_status",
            "on_market_future_exit_date",
        }

    asyncio.run(scenario())


@pytest.mark.parametrize("is_pg", [False, True], ids=["sqlite", "postgres"])
def test_market_status_sql_is_dialect_neutral(is_pg):
    """The market status fragment must render the same for both databases.

    The rest of the index build differs per dialect (STRING_AGG vs GROUP_CONCAT,
    REGEXP_REPLACE vs SUBSTR), so it is worth pinning that this addition does not
    reach for anything dialect specific. Execution itself is covered against
    SQLite by the tests above.
    """
    engine = GenericSQLDrugSearchEngine()
    sql = engine._build_index_insert_sql(
        searchable_attrs=[],
        searchable_multi=[],
        searchable_ref=[],
        searchable_multi_ref=[],
        searchable_codes=[],
        is_pg=is_pg,
        market_accessability=MarketAccessabilityDefinition(
            field_name=MARKET_FIELD,
            accessable_values=[ON_MARKET],
        ),
    )
    assert "market_accessable" in sql
    assert f"field_name = '{MARKET_FIELD}'" in sql
    assert f"ma.value IN ('{ON_MARKET}')" in sql
    assert "LEFT JOIN ma ON ma.drug_id = d.id" in sql

    # without a declaration the column is written, but always as NULL
    plain_sql = engine._build_index_insert_sql(
        searchable_attrs=[],
        searchable_multi=[],
        searchable_ref=[],
        searchable_multi_ref=[],
        searchable_codes=[],
        is_pg=is_pg,
        market_accessability=None,
    )
    assert "market_accessable" in plain_sql
    assert "drug_attr_ref_val" not in plain_sql
