from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import FastAPI, Request, Depends, status
from fastapi.security.open_id_connect_url import OpenIdConnect
from oauthlib.oauth2 import OAuth2Token
from authlib.oidc.core.claims import UserInfo as OIDCUserInfo

# intern imports
from medlogserver.config import Config
from medlogserver.REST_api.auth.jwt import JWTTokenContainer
from medlogserver.db.user import UserCRUD, User

config = Config()

from medlogserver.log import get_logger

log = get_logger()


class HTTPExceptionResponse(BaseModel):
    status_code: int
    detail: str


class OAuthErrorHTTPResponse(HTTPExceptionResponse):
    _error_code = 401

    @classmethod
    def from_OAuthError(cls, error: OAuthError):
        return cls(status_code=cls._error_code.default, detail=error.description)


def register_oidc_providers(app: FastAPI):
    for oidc_provider in config.AUTH_OIDC_PROVIDERS:
        authlib_oauth = OAuth()

        authlib_oauth.register(
            name="medlog",
            server_metadata_url=str(oidc_provider.DISCOVERY_ENDPOINT),
            client_kwargs={"scope": " ".join(oidc_provider.SCOPES)},
            client_id=oidc_provider.client_id,  # if enabled, authlib will also check that the access token belongs to this client id (audience)
            client_secret=oidc_provider.CLIENT_SECRET.get_secret_value(),
        )

        authlib_oauth_app: StarletteOAuth2App = authlib_oauth.medlog

        fastapi_oauth2_oidc = OpenIdConnect(
            openIdConnectUrl=str(oidc_provider.discovery_endpoint),
            scheme_name=oidc_provider.PROVIDER_NAME,
        )

        @app.get(f"/login/{oidc_provider.PROVIDER_NAME}")
        async def login(request: Request):
            # log.debug(request.session)
            # request.session['test'] = 'foo'
            redirect_uri = request.url_for("auth")
            log.debug(f"/login redirect_uri:{redirect_uri}")

            return await authlib_oauth_app.authorize_redirect(
                request, str(redirect_uri)
            )

        @app.get(
            f"/auth/{oidc_provider.PROVIDER_NAME}",
            # response_model=JWTTokenResponse,
            responses={401: {"model": OAuthErrorHTTPResponse}},
            response_description="a OAuth2Token token to be used to authenticate against the API",
        )
        async def auth(request: Request):
            # log.debug(request.session.get('test', ''))
            try:
                # We use the OAuth2 Authorization Code Flow. That means the OIDC provider send the auth code to here.
                # we create the refresh and access token from the auth code and send the access token back to the user
                print(request.session)
                user_oauth_token: OAuth2Token = (
                    await authlib_oauth_app.authorize_access_token(request)
                )
                log.info(f"token: {type(user_oauth_token)},{user_oauth_token}")

            except OAuthError as error:
                return OAuthErrorHTTPResponse.from_OAuthError(error)
            # <=0.15
            # user = await oauth.google.parse_id_token(request, token)
            try:
                userinfo: OIDCUserInfo = await authlib_oauth_app.userinfo(
                    token={"access_token": user_oauth_token["access_token"]}
                )
            except Exception as exp:
                log.error(f"Could not get userinfo from OIDC provider: {exp}")
            return user_oauth_token
