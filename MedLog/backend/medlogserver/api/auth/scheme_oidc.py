from typing import Generator, Dict
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client.apps import StarletteOAuth2App
from fastapi import FastAPI, Request, Depends, status, APIRouter, HTTPException
from fastapi.security.open_id_connect_url import OpenIdConnect
from oauthlib.oauth2 import OAuth2Token
from authlib.oidc.core.claims import UserInfo as OIDCUserInfo
from pydantic import BaseModel, ValidationError


# intern imports
from medlogserver.config import Config
from medlogserver.api.auth.model_token import (
    JWTRefreshTokenResponse,
    JWTRefreshTokenContainer,
    JWTAccessTokenContainer,
    JWTBundleTokenResponse,
)
from medlogserver.api.base import HTTPErrorResponeRepresentation
from medlogserver.db.user import User, UserCRUD, UserUpdate, UserUpdateByAdmin
from medlogserver.db.user_auth import (
    UserAuthCreate,
    UserAuthCRUD,
    AllowedAuthSourceTypes,
)

from medlogserver.db.user_auth_refresh_token import (
    UserAuthRefreshTokenCRUD,
    UserAuthRefreshTokenCreate,
)

from medlogserver.db.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
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
        self.oidc_provider_auth_url = (
            f"/auth/oidc/token/{oidc_provider_config.PROVIDER_SLUG_NAME}"
        )
        self.fast_api_router.add_api_route(
            path=f"/auth/oidc/login/{oidc_provider_config.PROVIDER_SLUG_NAME}",
            endpoint=self.login,
            name=f"login_{self.name}",
            methods=["GET"],
            description=f"Redirect to login with the external OpenID Connect provider '{oidc_provider_config.PROVIDER_DISPLAY_NAME}'",
        )
        self.fast_api_router.add_api_route(
            path=self.oidc_provider_auth_url,
            endpoint=self.auth,
            name=self.name,
            methods=["GET"],
            responses={401: {"model": HTTPErrorResponeRepresentation}},
            response_model=JWTBundleTokenResponse,
            response_description="a OAuth2Token token to be used to authenticate against the API",
            description=f"The 'Redirect URIs' for the external OpenID Connect providers '{oidc_provider_config.PROVIDER_DISPLAY_NAME}' token transfer",
        )

    @property
    def app(self) -> StarletteOAuth2App:
        return getattr(self.starlette_client, self.name)

    # ROUTE: /login
    async def login(self, request: Request):
        # log.info("YOOOO", self.name)
        redirect_uri = request.url_for(self.name)
        log.info(("HERWEGOJO", str(redirect_uri)))
        redirect_uri = str(config.get_server_url()).strip("/")
        if str(config.get_server_url()).strip("/") != str(config.CLIENT_URL).strip("/"):
            log.warning("Check if this is working: 7326472")
            redirect_uri = str(config.CLIENT_URL).strip("/")
        redirect_uri += "/login/oidc"
        return await self.app.authorize_redirect(request, str(redirect_uri))

    # ROUTE: /auth
    async def auth(
        self,
        request: Request,
        code: str = None,
        state: str = None,
        user_crud: UserCRUD = Depends(UserCRUD.get_crud),
        user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
        user_auth_access_token_crud: UserAuthRefreshTokenCRUD = Depends(
            UserAuthRefreshTokenCRUD.get_crud
        ),
        user_auth_external_oidc_token_crud: UserAuthExternalOIDCTokenCRUD = Depends(
            UserAuthExternalOIDCTokenCRUD.get_crud
        ),
    ):
        if code:
            # we are here after a successfull redirect from authentik/our-openidconnect-provider
            # log.info("######code", code)
            pass

        try:
            log.debug(("request.query_params", request.query_params))
            # We use the OAuth2 Authorization Code Flow. That means the OIDC provider send the auth code to here.
            # we create the refresh and access token from the auth code and send the access token back to the user
            user_oauth_token: OAuth2Token = await self.app.authorize_access_token(
                request
            )
            log.debug(("user_oauth_token", user_oauth_token))
            # log.debug(f"token: {type(user_oauth_token)},{user_oauth_token}")

        except OAuthError as error:
            log.error(error.description)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=error.description)

        # <=0.15
        # user = await oauth.google.parse_id_token(request, token)
        try:
            userinfo: OIDCUserInfo = await self.app.userinfo(
                token={"access_token": user_oauth_token["access_token"]}
            )
            log.debug(f"Userinfo from OIDC Provider endpoint: {userinfo}")
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
            log.debug(f"Userinfo extracted from OIDC token: {userinfo}")

        user_name_attribute = self.oidc_provider_config.USER_ID_ATTRIBUTE
        try:
            log.debug(("user_name_attribute", user_name_attribute))
            log.debug(("userinfo", userinfo))

            outer_userinfo = None
            if "userinfo" in userinfo:
                outer_userinfo = userinfo
                userinfo = outer_userinfo["userinfo"]

            user_name = userinfo.get(user_name_attribute)
            if user_name is None:
                if outer_userinfo and "sub" in outer_userinfo:
                    user_name = outer_userinfo.get("sub")
                elif "sub" in userinfo:
                    user_name = userinfo.get("sub")
                else:
                    raise ValueError("No username")
        except Exception as ex:
            log.debug(f"Userinfo: {userinfo}")
            log.error(ex)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not extract OIDC user_name in endpoint or token from '{self.oidc_provider_config.PROVIDER_DISPLAY_NAME}'. ",
            )
        log.debug(("user_name", user_name))
        if self.oidc_provider_config.PREFIX_USER_ID_WITH_PROVIDER_NAME:
            user_name = f"{self.name}{user_name}"

        user = await user_crud.get_by_user_name(user_name)

        if user is None and self.oidc_provider_config.AUTO_CREATE_AUTHORIZED_USER:
            log.debug(f"Create new user based on OIDC userinfo: {userinfo}")
            log.debug(
                f"self.oidc_provider_config.USER_MAIL_ATTRIBUTE: {self.oidc_provider_config.USER_MAIL_ATTRIBUTE}"
            )
            log.debug(
                f"userinfo.get(self.oidc_provider_config.USER_MAIL_ATTRIBUTE, None): {userinfo.get(self.oidc_provider_config.USER_MAIL_ATTRIBUTE, None)}"
            )
            user = User(
                email=userinfo.get(self.oidc_provider_config.USER_MAIL_ATTRIBUTE, None),
                display_name=userinfo.get(
                    self.oidc_provider_config.USER_DISPLAY_NAME_ATTRIBUTE, None
                ),
                deactivated=False,
                is_email_verified=userinfo.get(
                    self.oidc_provider_config.USER_MAIL_VERIFIED_ATTRIBUTE, False
                ),
                user_name=user_name,
            )
            user = self.apply_oidc_group_to_roles_mapping(userinfo, user)
            log.debug(f"Write new user to database: {user}")
            try:
                user = await user_crud.create(user)
            except ValidationError as val_err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Userinfo not parsable: {val_err}.",
                )
        elif user is None and not self.oidc_provider_config.AUTO_CREATE_AUTHORIZED_USER:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User is not authorized to self register via OIDC Provider '{self.oidc_provider_config.PROVIDER_DISPLAY_NAME}'.",
            )
        else:
            # update userdata
            log.info(f"Update user data for {user.id}")
            log.debug(f"Updated userinfo: {userinfo}")
            user_update = UserUpdateByAdmin(
                email=userinfo.get(self.oidc_provider_config.USER_MAIL_ATTRIBUTE, None),
                display_name=userinfo.get(
                    self.oidc_provider_config.USER_DISPLAY_NAME_ATTRIBUTE, user_name
                ),
                roles=[],
                deactivated=False,
                is_email_verified=userinfo.get(
                    self.oidc_provider_config.USER_MAIL_VERIFIED_ATTRIBUTE, False
                ),
                user_name=user_name,
            )
            user_update = self.apply_oidc_group_to_roles_mapping(userinfo, user_update)
            log.debug(f"Write updated user to database {user_update}")
            user = await user_crud.update(user_update, user_id=user.id)
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
        # create access token
        refresh_token = JWTRefreshTokenContainer(user_id=user.id)
        access_token = JWTAccessTokenContainer(
            user=user, parent_refresh_token_id=refresh_token.id
        )

        # save refresh token to DB. that way we can revoke it if needed
        await user_auth_access_token_crud.create(
            UserAuthRefreshTokenCreate(
                user_auth_id=user_auth.id,
                token_encoded=access_token.jwt_token_encoded,
                valid_until_timestamp=access_token.exp,
            )
        )
        return refresh_token.to_token_set_response(access_token=access_token)

    def apply_oidc_group_to_roles_mapping(
        self, oidc_userinfo: Dict, user: User | UserUpdateByAdmin
    ) -> User | UserUpdateByAdmin:
        if self.oidc_provider_config.ADMIN_MAPPING_GROUPS:
            log.debug(f"Apply role mapping for user {user}")
            log.debug(f"oidc_userinfo: {oidc_userinfo}")
            roles = []
            user_oidc_groups = None
            if self.oidc_provider_config.USER_GROUP_ATTRIBUTE in oidc_userinfo:
                user_oidc_groups = oidc_userinfo.get(
                    self.oidc_provider_config.USER_GROUP_ATTRIBUTE, []
                )

                for oidc_admin_group in self.oidc_provider_config.ADMIN_MAPPING_GROUPS:
                    if oidc_admin_group in user_oidc_groups:
                        log.debug(
                            f"User gets role {config.ADMIN_ROLE_NAME} because of membership in OIDC group {oidc_admin_group}"
                        )
                        roles.append(config.ADMIN_ROLE_NAME)
                user.roles.extend(roles)
        return user


def generate_oidc_provider_auth_routhers() -> Generator[APIRouter, None, None]:

    for oidc_provider in config.AUTH_OIDC_PROVIDERS:
        authlib_oauth = StarletteOAuthProviderAppContainer(oidc_provider)
        yield authlib_oauth.fast_api_router
