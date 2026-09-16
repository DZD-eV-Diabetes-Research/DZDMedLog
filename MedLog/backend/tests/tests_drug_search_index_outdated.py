"""Regression test for https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/364

After a drug dataset update the new dataset is activated before the search index is
rebuilt. In that window the index still lists drugs of the old dataset. The search
result lookup only returns drugs of the current dataset and custom drugs, so the
result would silently contain fewer items than its `total_count`.

The search must therefore treat an index that was built for another dataset version
as not ready and answer with the same 425 as during an index build up.
"""

from typing import Any, Dict
import asyncio
import uuid

from utils import req


def _set_index_based_on_dataset_version_id(dataset_version_id: uuid.UUID | None):
    """Point the search index state at another dataset version and return the old value."""
    from sqlmodel import select
    from medlogserver.db._session import get_async_session_context
    from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
        GenericSQLDrugSearchState,
    )

    async def run():
        async with get_async_session_context() as session:
            state = (await session.exec(select(GenericSQLDrugSearchState))).one()
            previous = state.last_index_build_based_on_drug_datasetversion_id
            state.last_index_build_based_on_drug_datasetversion_id = dataset_version_id
            session.add(state)
            await session.commit()
            return previous

    return asyncio.run(run())


def _get_custom_drugs_dataset_version_id() -> uuid.UUID:
    from medlogserver.db._session import get_async_session_context
    from medlogserver.db.drug_data.drug_dataset_version import DrugDataSetVersionCRUD

    async def run():
        async with get_async_session_context() as session:
            async with DrugDataSetVersionCRUD.crud_context(session) as crud:
                return (await crud.get_custom()).id

    return asyncio.run(run())


def test_drug_search_denied_while_search_index_is_based_on_outdated_dataset():
    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import search_drugs

    # sanity: the search works with the index as it is
    req("api/drug/search", method="get", q={"search_term": "Aspirin"})

    # any existing dataset version other than the current one will do. The custom
    # drugs collection always exists and keeps the foreign key valid on PostgreSQL.
    previous = _set_index_based_on_dataset_version_id(
        _get_custom_drugs_dataset_version_id()
    )
    try:
        res: Dict[str, Any] = req(
            "api/drug/search",
            method="get",
            q={"search_term": "Aspirin"},
            expected_http_code=425,
        )
    finally:
        # always hand the index back in a usable state, otherwise every following
        # test in the session would fail on drug search
        _set_index_based_on_dataset_version_id(previous)

    assert "detail" in res, f"Expected an error detail in the 425 response, got {res}"

    # and the search is available again once the index matches the current dataset
    req("api/drug/search", method="get", q={"search_term": "Aspirin"})
