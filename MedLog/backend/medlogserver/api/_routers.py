from fastapi import APIRouter
from fastapi_users import fastapi_users


from medlogserver.api.auth import oidc_client, auth_backend

router = APIRouter(prefix="/v1")

router.include_router(
    fastapi_users.get_oauth_router(
        oauth_client=oidc_client,
        backend=auth_backend,
        state_secret="SECRET",
        get_user_manager=fastapi_users.get_user_manager,
    ),
    prefix="/auth/openid",
    tags=["auth"],
)
