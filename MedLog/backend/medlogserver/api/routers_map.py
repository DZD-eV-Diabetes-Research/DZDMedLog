from fastapi import APIRouter, FastAPI

API_ENDPOINTS_PREFIX = "/api"


def mount_fast_api_routers(fastapi_app: FastAPI):

    ### Health
    from medlogserver.api.routes.routes_healthcheck import fast_api_healthcheck_router

    fastapi_app.include_router(
        fast_api_healthcheck_router, tags=["Health"], prefix=API_ENDPOINTS_PREFIX
    )

    ### Config
    from medlogserver.api.routes.routes_config import fast_api_config_router

    fastapi_app.include_router(
        fast_api_config_router, tags=["Config"], prefix=API_ENDPOINTS_PREFIX
    )

    ### AUTH STUFF
    from medlogserver.api.routes.routes_auth import (
        fast_api_auth_base_router,
    )

    fastapi_app.include_router(
        fast_api_auth_base_router, tags=["Auth"], prefix=API_ENDPOINTS_PREFIX
    )

    ### USER SELF MANAGEMENT
    from medlogserver.api.routes.routes_user import fast_api_user_self_service_router

    fastapi_app.include_router(
        fast_api_user_self_service_router, tags=["User"], prefix=API_ENDPOINTS_PREFIX
    )
    ### USER MANAGEMENT
    from medlogserver.api.routes.routes_user_management import (
        fast_api_user_manage_router,
    )

    fastapi_app.include_router(
        fast_api_user_manage_router,
        tags=["User Admin"],
        prefix=API_ENDPOINTS_PREFIX,
    )

    ### APP - Business logic
    from medlogserver.api.routes.routes_study import fast_api_study_router

    fastapi_app.include_router(
        fast_api_study_router, tags=["Study"], prefix=API_ENDPOINTS_PREFIX
    )

    from medlogserver.api.routes.routes_study_permission import (
        fast_api_permissions_router,
    )

    fastapi_app.include_router(
        fast_api_permissions_router,
        tags=["Study Permissions"],
        prefix=API_ENDPOINTS_PREFIX,
    )

    ### Event

    from medlogserver.api.routes.routes_event import fast_api_event_router

    fastapi_app.include_router(
        fast_api_event_router, tags=["Event"], prefix=API_ENDPOINTS_PREFIX
    )

    ### Interview

    from medlogserver.api.routes.routes_interview import (
        fast_api_interview_router,
    )

    fastapi_app.include_router(
        fast_api_interview_router, tags=["Interview"], prefix=API_ENDPOINTS_PREFIX
    )

    ### Intake

    from medlogserver.api.routes.routes_intake import (
        fast_api_intake_router,
    )

    fastapi_app.include_router(
        fast_api_intake_router, tags=["Intake"], prefix=API_ENDPOINTS_PREFIX
    )
    ### Drug V2
    from medlogserver.api.routes.routes_drug import fast_api_drug_router

    fastapi_app.include_router(
        fast_api_drug_router, tags=["Drug"], prefix=API_ENDPOINTS_PREFIX
    )

    # export
    from medlogserver.api.routes.routes_export import fast_api_export_router

    fastapi_app.include_router(
        fast_api_export_router, tags=["Export"], prefix=API_ENDPOINTS_PREFIX
    )

    # webclient
    from medlogserver.api.routes.routes_webclient import fast_api_webclient_router

    fastapi_app.include_router(fast_api_webclient_router, tags=["WebClient"])
