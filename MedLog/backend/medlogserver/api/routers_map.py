from fastapi import APIRouter, FastAPI


def mount_fast_api_routers(fastapi_app: FastAPI):

    ### Health
    from medlogserver.api.routes.routes_healthcheck import fast_api_healthcheck_router

    fastapi_app.include_router(fast_api_healthcheck_router, tags=["Health"])

    ### AUTH STUFF
    from medlogserver.api.routes.routes_auth import (
        fast_api_auth_base_router,
    )

    fastapi_app.include_router(fast_api_auth_base_router, tags=["Auth"])

    from medlogserver.api.auth.scheme_local import fast_api_auth_local_router

    fastapi_app.include_router(fast_api_auth_local_router, tags=["Auth"])

    from medlogserver.api.routes.routes_user import (
        fast_api_user_manage_router,
    )
    from medlogserver.api.auth.scheme_oidc import (
        generate_oidc_provider_auth_routhers,
    )

    for oidc_provider_router in generate_oidc_provider_auth_routhers():
        fastapi_app.include_router(oidc_provider_router, tags=["Auth"])

    ### USER MANAGEMENT
    fastapi_app.include_router(fast_api_user_manage_router, tags=["User"])

    ### APP - Business logic
    from medlogserver.api.routes.routes_study import fast_api_study_router

    fastapi_app.include_router(fast_api_study_router, tags=["Study"])

    from medlogserver.api.routes.routes_study_permission import (
        fast_api_permissions_router,
    )

    fastapi_app.include_router(fast_api_permissions_router, tags=["Study Permissions"])

    ### Event

    from medlogserver.api.routes.routes_event import fast_api_event_router

    fastapi_app.include_router(fast_api_event_router, tags=["Event"])

    ### Interview

    from medlogserver.api.routes.routes_interview import (
        fast_api_interview_router,
    )

    fastapi_app.include_router(fast_api_interview_router, tags=["Interview"])

    ### Intake

    from medlogserver.api.routes.routes_intake import (
        fast_api_intake_router,
    )

    fastapi_app.include_router(fast_api_intake_router, tags=["Intake"])
    ### Drug V2
    from medlogserver.api.routes.routes_drug_v2 import fast_api_drug_router_v2

    fastapi_app.include_router(fast_api_drug_router_v2, tags=["Drug (Ver.2)"])

    # export
    from medlogserver.api.routes.routes_export import fast_api_export_router

    fastapi_app.include_router(fast_api_export_router, tags=["Export"])
    ### Drug V1
    from medlogserver.api.routes.routes_drug import (
        fast_api_drug_router,
    )

    fastapi_app.include_router(fast_api_drug_router, tags=["DrugV1(Deprecated)"])
