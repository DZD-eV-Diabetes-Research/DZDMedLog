"""Regression test for https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/37

A custom drug is the fallback for a drug the user could not find in the search.
Creating one with the name of an existing drug (from the current drug dataset or an
earlier custom drug) must be refused with HTTP 409, so the same drug does not end up
in the database several times.
"""

from typing import Any, Dict
import asyncio

from utils import req, dictyfy


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


def test_create_custom_drug_with_name_of_existing_custom_drug_is_refused():
    from medlogserver.model.drug_data.drug import DrugCustomCreate

    # import only as IDE Shortcut
    from medlogserver.api.routes.routes_drug import create_custom_drug

    trade_name = "Duplicate custom drug DUPLICATENAME37"
    first: Dict[str, Any] = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(DrugCustomCreate(trade_name=trade_name)),
    )
    assert first["trade_name"] == trade_name

    # same name, different case and surrounding whitespace
    for duplicate_name in [
        trade_name,
        trade_name.upper(),
        f"  {trade_name.lower()} ",
    ]:
        res: Dict[str, Any] = req(
            "api/drug/custom",
            method="post",
            b=dictyfy(DrugCustomCreate(trade_name=duplicate_name)),
            expected_http_code=409,
        )
        print("res", res)
        assert first["id"] in res["detail"], (
            f"Expected the 409 detail to point to the existing drug {first['id']}, got {res}"
        )
    assert _count_drugs_by_trade_name(trade_name) == 1


def test_create_custom_drug_with_name_of_dataset_drug_is_refused():
    from medlogserver.model.drug_data.drug import DrugCustomCreate

    # "Test2Drug" is part of the dummy drug dataset, see `create_test_study` in utils.py
    trade_name = "Test2Drug"
    drug_search_result = req(
        "api/drug/search", method="get", q={"search_term": trade_name}
    )
    dataset_drugs = [
        item["drug"]
        for item in drug_search_result["items"]
        if item["drug"]["trade_name"] == trade_name
        and not item["drug"]["is_custom_drug"]
    ]
    assert dataset_drugs, f"Dataset drug '{trade_name}' not found: {drug_search_result}"
    count_before = _count_drugs_by_trade_name(trade_name)

    res: Dict[str, Any] = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(DrugCustomCreate(trade_name=trade_name)),
        expected_http_code=409,
    )
    print("res", res)
    assert _count_drugs_by_trade_name(trade_name) == count_before


def test_create_custom_drug_with_similar_but_different_name_works():
    """The check must only match the whole name, not a part of it."""
    from medlogserver.model.drug_data.drug import DrugCustomCreate

    trade_name = "Duplicate custom drug DUPLICATENAME37 forte"
    res: Dict[str, Any] = req(
        "api/drug/custom",
        method="post",
        b=dictyfy(DrugCustomCreate(trade_name=trade_name)),
    )
    assert res["trade_name"] == trade_name
