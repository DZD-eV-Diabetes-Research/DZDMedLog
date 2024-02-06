from fastapi import APIRouter, FastAPI


def mount_fast_api_routers(fastapi_app: FastAPI):
    ### AUTH STUFF
    from medlogserver.REST_api.auth.base import fast_api_auth_base_router

    fastapi_app.include_router(fast_api_auth_base_router, tags=["Auth"])

    from medlogserver.REST_api.auth.scheme_local import fast_api_auth_local_router

    fastapi_app.include_router(fast_api_auth_local_router, tags=["Auth"])

    from medlogserver.REST_api.user.manage_local_users import (
        fast_api_user_manage_router,
    )
    from medlogserver.REST_api.auth.scheme_oidc import (
        generate_oidc_provider_auth_routhers,
    )

    for oidc_provider_router in generate_oidc_provider_auth_routhers():
        fastapi_app.include_router(oidc_provider_router, tags=["Auth"])

    ### USER MANAGEMENT
    fastapi_app.include_router(fast_api_user_manage_router, tags=["User"])

    ### APP - Business logic
    from medlogserver.REST_api.routes_app.routes_study import fast_api_study_router

    fastapi_app.include_router(fast_api_study_router, tags=["Study"])

    from medlogserver.REST_api.routes_app.routes_event import fast_api_event_router

    fastapi_app.include_router(fast_api_event_router, tags=["Event"])

    from medlogserver.REST_api.routes_app.routes_interview import (
        fast_api_interview_router,
    )

    fastapi_app.include_router(fast_api_interview_router, tags=["Interview"])

    from medlogserver.REST_api.routes_app.routes_intakes import (
        fast_api_intake_router,
    )

    fastapi_app.include_router(fast_api_intake_router, tags=["Intake"])
