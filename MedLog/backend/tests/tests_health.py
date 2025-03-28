from utils import req, dict_must_contain


def test_health():
    from medlogserver.api.routes.routes_healthcheck import get_health_status

    res = req("health")
    print(res)
    dict_must_contain(res, required_keys_and_val={"healthy": True})


def test_health_report():
    from medlogserver.api.routes.routes_healthcheck import get_health_report

    res = req("health/report")
    dict_must_contain(
        res,
        required_keys_and_val={
            "name": "DZDMedLog",
            "db_working": True,
            "drugs_imported": True,
            "last_worker_run_succesfull": True,
            "drug_search_index_working": True,
        },
    )
    print(res)


def test_do_health():
    test_health()
    test_health_report()


a = {
    "name": "DZDMedLog",
    "version": "0.0.0",
    "db_working": True,
    "drugs_imported": False,
    "last_worker_run_succesfull": True,
    "drug_search_index_working": False,
}
