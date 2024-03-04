from fastapi import APIRouter, FastAPI


def mount_fast_api_routers(fastapi_app: FastAPI):
    ### AUTH STUFF
    from medlogserver.api.auth.routes_base import fast_api_auth_base_router

    fastapi_app.include_router(fast_api_auth_base_router, tags=["Auth"])

    from medlogserver.api.auth.scheme_local import fast_api_auth_local_router

    fastapi_app.include_router(fast_api_auth_local_router, tags=["Auth"])

    from medlogserver.api.user.manage_local_users import (
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
    from medlogserver.api.routes_app.routes_study import fast_api_study_router

    fastapi_app.include_router(fast_api_study_router, tags=["Study"])

    from api.routes_app.routes_study_permission import (
        fast_api_permissions_router,
    )

    fastapi_app.include_router(fast_api_permissions_router, tags=["Study Permissions"])

    from medlogserver.api.routes_app.routes_event import fast_api_event_router

    fastapi_app.include_router(fast_api_event_router, tags=["Event"])

    from medlogserver.api.routes_app.routes_interview import (
        fast_api_interview_router,
    )

    fastapi_app.include_router(fast_api_interview_router, tags=["Interview"])

    from api.routes_app.routes_intake import (
        fast_api_intake_router,
    )

    fastapi_app.include_router(fast_api_intake_router, tags=["Intake"])

    from api.routes_app.routes_drug import (
        fast_api_drug_router,
    )

    fastapi_app.include_router(fast_api_drug_router, tags=["Drug"])
