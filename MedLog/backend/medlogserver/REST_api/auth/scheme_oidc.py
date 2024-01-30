from typing import Generator
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import FastAPI, Request, Depends, status, APIRouter, HTTPException
from fastapi.security.open_id_connect_url import OpenIdConnect
from oauthlib.oauth2 import OAuth2Token
from authlib.oidc.core.claims import UserInfo as OIDCUserInfo
from pydantic import BaseModel


# intern imports
from medlogserver.config import Config
from medlogserver.REST_api.auth.jwt import JWTTokenContainer
from medlogserver.REST_api.base import HTTPErrorResponeRepresentation
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
from medlogserver.REST_api.auth.jwt import JWTTokenResponse
from medlogserver.db.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


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
            responses={401: {"model": HTTPErrorResponeRepresentation}},
            response_model=JWTTokenResponse,
            response_description="a OAuth2Token token to be used to authenticate against the API",
        )

    @property
    def app(self) -> StarletteOAuth2App:
        return getattr(self.starlette_client, self.name)

    async def login(self, request: Request):
        redirect_uri = request.url_for(self.name)
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
        try:
            # We use the OAuth2 Authorization Code Flow. That means the OIDC provider send the auth code to here.
            # we create the refresh and access token from the auth code and send the access token back to the user
            user_oauth_token: OAuth2Token = await self.app.authorize_access_token(
                request
            )
            log.info(f"token: {type(user_oauth_token)},{user_oauth_token}")

        except OAuthError as error:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=error.description)

        # <=0.15
        # user = await oauth.google.parse_id_token(request, token)
        try:
            userinfo: OIDCUserInfo = await self.app.userinfo(
                token={"access_token": user_oauth_token["access_token"]}
            )
        except Exception as exp:
            # extract user info from token if userinfo endpoint did not work
            claims = OIDCUserInfo.REGISTERED_CLAIMS + [
                self.oidc_provider_config.USER_ID_ATTRIBUTE,
                self.oidc_provider_config.USER_DISPLAY_NAME_ATTRIBUTE,
                self.oidc_provider_config.USER_MAIL_ATTRIBUTE,
                self.oidc_provider_config.USER_MAIL_VERIFIED_ATTRIBUTE,
                self.oidc_provider_config.USER_GROUP_ATTRIBUTE,
            ]
            userinfo = OIDCUserInfo()
            for claim in claims:
                userinfo[claim] = user_oauth_token.get(claim, None)

        username_attribute = self.oidc_provider_config.USER_ID_ATTRIBUTE
        try:
            username = userinfo.get(username_attribute)
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not extract OIDC username in endpoint or token from '{self.oidc_provider_config.PROVIDER_DISPLAY_NAME}'.",
            )
        if self.oidc_provider_config.PREFIX_USER_ID_WITH_PROVIDER_NAME:
            username = f"{self.name}{username}"

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
            user = await user_crud.create(user)
        elif user is None and not self.oidc_provider_config.AUTO_CREATE_AUTHORIZED_USER:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User is not authorized to self register via OIDC Provider '{self.oidc_provider_config.PROVIDER_DISPLAY_NAME}'.",
            )
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
        await user_auth_access_token_crud.create(
            UserAuthAccessTokenCreate(
                user_auth_id=user_auth.id,
                token_encoded=access_token.jwt_token_encoded,
                valid_until_timestamp=int(access_token.exp),
            )
        )

        return access_token.get_response()


def generate_oidc_provider_auth_routhers() -> Generator[APIRouter, None, None]:
    print("config.AUTH_OIDC_PROVIDERS", config.AUTH_OIDC_PROVIDERS)
    for oidc_provider in config.AUTH_OIDC_PROVIDERS:
        authlib_oauth = StarletteOAuthProviderAppContainer(oidc_provider)
        yield authlib_oauth.fast_api_router
