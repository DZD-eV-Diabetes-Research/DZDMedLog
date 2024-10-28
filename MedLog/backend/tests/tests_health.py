from utils import req, dict_must_contain


def test_health():
    from medlogserver.api.routes.routes_healthcheck import get_health_status

    req("health/")


def test_health_report():
    from medlogserver.api.routes.routes_healthcheck import get_health_report

    res = req("health/report")
    dict_must_contain(
        res,
    )


a = {
    "name": "DZDMedLog",
    "version": "0.0.0",
    "db_working": True,
    "drugs_imported": False,
    "last_worker_run_succesfull": True,
    "drug_search_index_working": False,
}
