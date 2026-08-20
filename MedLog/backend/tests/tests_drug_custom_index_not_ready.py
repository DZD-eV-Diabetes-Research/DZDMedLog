"""Regression test for https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/232

Creating a custom drug is the "I could not find this drug in the search"-fallback.
That only makes sense if the user was able to search in the first place, so
`POST /api/drug/custom` must refuse as long as the drug search index is not ready.

Before the fix the endpoint created (and committed) the drug first and only
afterwards ran the search index preflight. With a not-ready index that preflight
raised an uncaught `SearchEngineNotReadyException` -> the client got a HTTP 500
while the drug was already persisted but missing from the index.
"""

from typing import Any, Dict
import asyncio

from utils import req, dictyfy


def _set_index_build_up_in_process(in_process: bool):
    """Put the drug search index into/out of the 'still building' state.

    `DrugSearch._preflight()` decides via `index_ready()`, which reads exactly this
    flag from `drug_search_generic_sql_state`. Flipping it is the cheapest way to
    simulate a still building index against the running test server.
    """
    from sqlmodel import select
    from medlogserver.db._session import get_async_session_context
    from medlogserver.db.drug_data.drug_search.search_module_generic_sql import (
        GenericSQLDrugSearchState,
    )
    from medlogserver.utils import get_now_datetime

    async def run():
        async with get_async_session_context() as session:
            state = (await session.exec(select(GenericSQLDrugSearchState))).one()
            state.index_build_up_in_process = in_process
            # `build_index()` considers a lock older than 6h stale and would reset it.
            # Keep the timestamp fresh so a concurrent worker tick leaves it alone.
            state.index_build_started_at = get_now_datetime() if in_process else None
            session.add(state)
            await session.commit()

    asyncio.run(run())


def _count_drugs_by_trade_name(trade_name: str) -> int:
    from sqlmodel import select
    from medlogserver.db._session import get_async_session_context
    from medlogserver.model.drug_data import DrugData

    async def run():
        async with get_async_session_context() as session:
            res = await session.exec(
                select(DrugData).where(DrugData.trade_name == trade_name)
            )
            return len(res.all())

    return asyncio.run(run())


def test_create_custom_drug_denied_while_search_index_not_ready():
    """POST /api/drug/custom must answer 503 and create nothing while the index builds."""
    from medlogserver.model.drug_data.drug import DrugCustomCreate

    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug

    trade_name = "Custom drug attempted during index build INDEXNOTREADY232"
    custom_drug_payload = DrugCustomCreate(trade_name=trade_name)

    _set_index_build_up_in_process(True)
    try:
        res: Dict[str, Any] = req(
            "api/drug/custom",
            method="post",
            b=dictyfy(custom_drug_payload),
            expected_http_code=503,
        )
    finally:
        # always hand the index back in a usable state, otherwise every following
        # test in the session would fail on drug search
        _set_index_build_up_in_process(False)

    print("res", res)
    assert "detail" in res, f"Expected an error detail in the 503 response, got {res}"

    # the request must not have left a half created drug behind
    leftover_count = _count_drugs_by_trade_name(trade_name)
    assert leftover_count == 0, (
        f"Expected no drug to be created when the search index is not ready, "
        f"but found {leftover_count} drug(s) named '{trade_name}' in the database."
    )


def test_create_custom_drug_works_again_when_search_index_is_ready():
    """Counterpart to the test above: the guard must not block the normal case."""
    from medlogserver.model.drug_data.drug import DrugCustomCreate

    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug

    trade_name = "Custom drug created with ready index INDEXREADY232"
    custom_drug_payload = DrugCustomCreate(trade_name=trade_name)

    res: Dict[str, Any] = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(custom_drug_payload),
    )
    print("res", res)
    assert res["trade_name"] == trade_name

    # and it is searchable right away, so the index insert still happens
    drug_search_result = req(
        "api/drug/search", method="get", q={"search_term": "INDEXREADY232"}
    )
    assert [
        item for item in drug_search_result["items"] if item["drug_id"] == res["id"]
    ], f"Custom drug '{trade_name}' was not found in the search index: {drug_search_result}"
