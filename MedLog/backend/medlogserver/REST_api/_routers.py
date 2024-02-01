from fastapi import APIRouter, FastAPI


def mount_fast_api_routers(fastapi_app: FastAPI):
    ### AUTH STUFF
    from medlogserver.REST_api.auth.base import fast_api_auth_base_router

    fastapi_app.include_router(fast_api_auth_base_router, tags=["Auth"])

    from medlogserver.REST_api.auth.scheme_local import fast_api_auth_local_router

    fastapi_app.include_router(fast_api_auth_local_router, tags=["Auth"])

    from medlogserver.REST_api.auth.scheme_oidc import (
        generate_oidc_provider_auth_routhers,
    )

    for oidc_provider_router in generate_oidc_provider_auth_routhers():
        fastapi_app.include_router(oidc_provider_router, tags=["Auth"], prefix="/oidc")
