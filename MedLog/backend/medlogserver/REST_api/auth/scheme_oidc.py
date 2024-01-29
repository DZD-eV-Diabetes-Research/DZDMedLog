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
    UserAuthCreate,
    UserAuthCRUD,
    UserAuthAccessToken,
    UserAuthAccessTokenCreate,
    UserAuthAccessTokenCRUD,
    get_user_auth_access_token_crud,
    AllowedAuthSourceTypes,
)
from medlogserver.db.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
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


class StarletteOAuthProviderAppContainer:
    def __init__(self, oidc_provider_config: Config.OpenIDConnectProvider):
        self.name = f"medlog{oidc_provider_config.PROVIDER_SLUG_NAME.replace('-','')}"
        self.oidc_provider_config = oidc_provider_config
        self.fast_api_router: APIRouter = APIRouter()
        self.starlette_client = OAuth()

        self.starlette_client.register(
            name=self.name,
            server_metadata_url=str(oidc_provider_config.DISCOVERY_ENDPOINT),
            client_kwargs={"scope": " ".join(oidc_provider_config.SCOPES)},
            client_id=oidc_provider_config.CLIENT_ID,  # if enabled, authlib will also check that the access token belongs to this client id (audience)
            client_secret=oidc_provider_config.CLIENT_SECRET.get_secret_value(),
        )
        # this is the url the external OIDC provider will be redirect to (at our API here) after the user has authenticated
        self.oidc_provider_auth_url = f"/auth/{oidc_provider_config.PROVIDER_SLUG_NAME}"
        self.fast_api_router.add_api_route(
            path=f"/login/{oidc_provider_config.PROVIDER_SLUG_NAME}",
            endpoint=self.login,
            name=f"login_{self.name}",
            methods=["GET"],
        )
        self.fast_api_router.add_api_route(
            path=self.oidc_provider_auth_url,
            endpoint=self.auth,
            name=self.name,
            methods=["GET"],
            responses={401: {"model": OAuthErrorHTTPResponse}},
            response_description="a OAuth2Token token to be used to authenticate against the API",
        )

    @property
    def app(self) -> StarletteOAuth2App:
        return getattr(self.starlette_client, self.name)

    async def login(self, request: Request):
        redirect_uri = request.url_for(self.name)
        log.debug(f"/login redirect_uri:{redirect_uri}")

        return await self.app.authorize_redirect(request, str(redirect_uri))

    async def auth(
        self,
        request: Request,
        user_crud: UserCRUD = Depends(get_users_crud),
        user_auth_crud: UserAuthCRUD = Depends(get_user_auth_crud),
        user_auth_access_token_crud: UserAuthAccessTokenCRUD = Depends(
            get_user_auth_access_token_crud
        ),
        user_auth_external_oidc_token_crud: UserAuthExternalOIDCTokenCRUD = Depends(
            get_user_auth_external_oidc_token_crud
        ),
    ):
        # TIM YOU ARE HERE

        # log.debug(request.session.get('test', ''))
        try:
            # We use the OAuth2 Authorization Code Flow. That means the OIDC provider send the auth code to here.
            # we create the refresh and access token from the auth code and send the access token back to the user
            user_oauth_token: OAuth2Token = await self.app.authorize_access_token(
                request
            )
            log.info(f"token: {type(user_oauth_token)},{user_oauth_token}")

        except OAuthError as error:
            return OAuthErrorHTTPResponse.from_OAuthError(error)
        # <=0.15
        # user = await oauth.google.parse_id_token(request, token)
        try:
            userinfo: OIDCUserInfo = await self.app.userinfo(
                token={"access_token": user_oauth_token["access_token"]}
            )
        except Exception as exp:
            # todo: if the endpoint is not available/functional we can try to extract the userinfo from the token.
            log.error(f"Could not get userinfo from OIDC provider: {exp}")
            raise ValueError("Can not reach userendpoint. TODO: Proper Error message")
        username_attribute = self.oidc_provider_config.USER_ID_ATTRIBUTE

        username = f"{self.oidc_provider_config.PREFIX_USER_ID_WITH_PROVIDER_NAME if not None else ''}{userinfo.get(username_attribute)}"

        user = await user_crud.get_by_username(username)
        if user is None and self.oidc_provider_config.AUTO_CREATE_AUTHORIZED_USER:
            user = User(
                email=userinfo.get(self.oidc_provider_config.USER_MAIL_ATTRIBUTE, None),
                display_name=userinfo.get(
                    self.oidc_provider_config.USER_DISPLAY_NAME_ATTRIBUTE, None
                ),
                roles=userinfo.get(
                    self.oidc_provider_config.USER_GROUP_ATTRIBUTE, None
                ),
                disabled=False,
                is_email_verified=userinfo.get(
                    self.oidc_provider_config.USER_MAIL_VERIFIED_ATTRIBUTE, False
                ),
                username=username,
            )
            print("USER PRE CREATE", user)
            user = await user_crud.create(user)
            print("USER POST CREATE", user)
        elif user is None and not self.oidc_provider_config.AUTO_CREATE_AUTHORIZED_USER:
            raise ValueError("Not allowed to create user")
        user_auth = await user_auth_crud.list_by_user_id(
            user.id,
            filter_auth_source_type=AllowedAuthSourceTypes.oidc,
            filter_oidc_provider_name=self.name,
        )
        if not user_auth:
            user_auth = await user_auth_crud.create(
                UserAuthCreate(
                    user_id=user.id,
                    auth_source_type=AllowedAuthSourceTypes.oidc,
                    oidc_provider_name=self.name,
                )
            )
        else:
            user_auth = user_auth[0]
        user_auth_external_oidc_token = await user_auth_external_oidc_token_crud.create(
            UserAuthExternalOIDCToken(
                oidc_provider_name=self.name,
                oauth_token=user_oauth_token,
                user_auth_id=user_auth.id,
            )
        )
        access_token = JWTTokenContainer(user=user)
        print(
            "access_token.exp_timestamp_utc",
            access_token.exp_timestamp_utc,
            type(access_token.exp_timestamp_utc),
        )
        await user_auth_access_token_crud.create(
            UserAuthAccessTokenCreate(
                user_auth_id=user_auth.id,
                token_encoded=access_token.jwt_token_encoded,
                valid_until_timestamp=int(access_token.exp_timestamp_utc),
            )
        )

        return access_token.get_response()


def generate_oidc_provider_auth_routhers() -> Generator[APIRouter, None, None]:
    for oidc_provider in config.AUTH_OIDC_PROVIDERS:
        authlib_oauth = StarletteOAuthProviderAppContainer(oidc_provider)
        yield authlib_oauth.fast_api_router
