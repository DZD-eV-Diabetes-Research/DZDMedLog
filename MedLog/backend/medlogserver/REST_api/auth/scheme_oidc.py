from typing import Generator
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import FastAPI, Request, Depends, status
from fastapi.security.open_id_connect_url import OpenIdConnect
from oauthlib.oauth2 import OAuth2Token
from authlib.oidc.core.claims import UserInfo as OIDCUserInfo
from pydantic import BaseModel
from fastapi import APIRouter

# intern imports
from medlogserver.config import Config
from medlogserver.REST_api.auth.jwt import JWTTokenContainer
from medlogserver.db.user import get_users_crud, User, UserCRUD
from medlogserver.db.user_auth import (
    get_user_auth_crud,
    UserAuth,
    UserAuthCRUD,
    UserAuthAccessToken,
    UserAuthAccessTokenCRUD,
    get_user_auth_access_token_crud,
)

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


def register_oidc_providers() -> Generator[APIRouter, None, None]:
    # TODO: test if function names of route muste be unique for multiple OIDC providers
    for oidc_provider in config.AUTH_OIDC_PROVIDERS:
        oidc_router = APIRouter()
        # this is the url the external OIDC provider will be redirect to (at our API here) after the user has authenticated
        oidc_provider_auth_url = f"/auth/{oidc_provider.PROVIDER_SLUG_NAME}"
        oauthname = f"medlog{oidc_provider.PROVIDER_SLUG_NAME.replace('-','')}"
        authlib_oauth = OAuth()

        authlib_oauth.register(
            name=oauthname,
            server_metadata_url=str(oidc_provider.DISCOVERY_ENDPOINT),
            client_kwargs={"scope": " ".join(oidc_provider.SCOPES)},
            client_id=oidc_provider.CLIENT_ID,  # if enabled, authlib will also check that the access token belongs to this client id (audience)
            client_secret=oidc_provider.CLIENT_SECRET.get_secret_value(),
        )

        authlib_oauth_app: StarletteOAuth2App = getattr(authlib_oauth, oauthname)

        """
        fastapi_oauth2_oidc = OpenIdConnect(
            openIdConnectUrl=str(oidc_provider.DISCOVERY_ENDPOINT),
            scheme_name=oidc_provider.PROVIDER_SLUG_NAME,
        )
        """

        @oidc_router.get(
            f"/login/{oidc_provider.PROVIDER_SLUG_NAME}",
            name=f"login_{oauthname}",
        )
        async def login(request: Request):
            redirect_uri = request.url_for(oauthname)
            log.debug(f"/login redirect_uri:{redirect_uri}")

            return await authlib_oauth_app.authorize_redirect(
                request, str(redirect_uri)
            )

        @oidc_router.get(
            oidc_provider_auth_url,
            name=oauthname,
            # response_model=JWTTokenResponse,
            responses={401: {"model": OAuthErrorHTTPResponse}},
            response_description="a OAuth2Token token to be used to authenticate against the API",
        )
        async def auth(
            request: Request,
            user_crud: UserCRUD = Depends(get_users_crud),
            user_auth_crud: UserAuthCRUD = Depends(get_user_auth_crud),
            user_auth_access_token_crud: UserAuthAccessTokenCRUD = Depends(
                get_user_auth_access_token_crud
            ),
        ):
            # TIM YOU ARE HERE

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

        yield oidc_router
