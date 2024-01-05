from httpx_oauth.clients.openid import OpenID
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from medlogserver.config import Config

config = Config()

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=config.oidc.jwt_secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# configure the OpenID Connect Client.
# based on https://frankie567.github.io/httpx-oauth/oauth2/#openid
# and https://fastapi-users.github.io/fastapi-users/12.1/configuration/oauth/#instantiate-an-oauth2-client
oidc_client = OpenID(
    client_id=config.oidc.client_id,
    client_secret=config.oidc.client_secret,
    openid_configuration_endpoint=str(config.oidc.discovery_endpoint),
    name="openid",
    base_scopes=config.oidc.scopes,
)
