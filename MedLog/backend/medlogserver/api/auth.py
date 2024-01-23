import logging
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.open_id_connect_url import OpenIdConnect
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.integrations.starlette_client.apps import StarletteOAuth2App

from jose import JWTError, jwt
from oauthlib.oauth2 import OAuth2Token

from fastapi import HTTPException
from fastapi import Request
from fastapi import Depends
from fastapi import status
from typing import Optional, List, Literal
from typing_extensions import Self

from authlib.oidc.core.claims import UserInfo as OIDCUserInfo

# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()

config = Config()


class HTTPExceptionResponse(BaseModel):
    status_code: int
    detail: str


class OAuthErrorHTTPResponse(HTTPExceptionResponse):
    _error_code = 401

    @classmethod
    def from_OAuthError(cls, error: OAuthError):
        return cls(status_code=cls._error_code.default, detail=error.description)

class JWTTokenResponse(BaseModel):
    token: str = Field(
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
        description="JWT token to be used to authenticate against the API",
    )
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(
        description="The number of seconds until the token expires", examples=[3600]
    )


class JWTTokenContainer:
    def __init__(
        self,
        sub: str,
        scope: List[str] = None,
        prevent_generate_new_token: bool = False,
    ):
        """_summary_

        Args:
            sub (str): "Subject" - the user name/id
            scope (List[str], optional): _description_. Defaults to None.
            prevent_generate_new_token (bool, optional): _description_. Defaults to False.
        """
        if scope is None:
            scope = []
        self.scope: List[str] = scope
        self.sub: str = sub
        self.exp: datetime = None
        self.jwt_token: str = None
        if not prevent_generate_new_token:
            self._generate_token()

    def get_response(self) -> JWTTokenResponse:
        return JWTTokenResponse(
            token=self.jwt_token,
            token_type="Bearer",
            expires_in=int((self.exp - datetime.now(timezone.utc)).total_seconds()),
        )

    def _generate_token(self):
        expire_moment: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=config.JWT_TOKEN_EXPIRES_MINUTES
        )
        self.exp = expire_moment
        self.jwt_token = jwt.encode(
            claims={
                "sub": self.sub,
                "exp": self.exp.timestamp(),
                "aud": str(config.get_server_url()),
                "scope": " ".join(self.scope),
                "iss": config.SERVER_HOSTNAME,
            },
            key=config.JWT_SECRET,
            algorithm=config.JWT_ALGORITHM,
        )

    @classmethod
    def from_existing_jwt(cls, jwt_token: str) -> Self:
        try:
            jwt_token_decoded = jwt.decode(
                jwt_token, config.JWT_SECRET, config.JWT_ALGORITHM
            )
            new_obj = cls(
                user_name=jwt_token_decoded["sub"],
                user_roles=jwt_token_decoded["scope"].split(" "),
                prevent_generate_new_token=True,
            )
            new_obj.jwt_token = jwt_token
            new_obj.exp = datetime.fromtimestamp(jwt_token_decoded["exp"])
            return new_obj
        except JWTError as exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supplied authentication could not be validated ({exp})",
            )


app = FastAPI(
    #swagger_ui_oauth2_redirect_url='/auth',
    swagger_ui_init_oauth={
        "clientId": config.oidc.client_id,
        "appName": "medlog",
        "scopeSeparator": " ",
        "additionalQueryStringParams": {},
        "scopes": "openid profile email",
        "useBasicAuthenticationWithAccessCodeGrant": False,
        "usePkceWithAuthorizationCodeGrant": False,
    }
)

#app.add_middleware(SessionMiddleware, secret_key=config.oidc.jwt_secret)
app.add_middleware(SessionMiddleware,secret_key="xxx")
# TODO FIX THIS: ONLY FOR DEV
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


authlib_oauth = OAuth()


authlib_oauth.register(
    name="medlog",
    server_metadata_url=str(config.oidc.discovery_endpoint),
    client_kwargs={"scope": " ".join(config.oidc.scopes)},
    client_id=config.oidc.client_id,  # if enabled, authlib will also check that the access token belongs to this client id (audience)
    client_secret=config.oidc.client_secret.get_secret_value(),
)

authlib_oauth_app: StarletteOAuth2App = authlib_oauth.medlog

fastapi_oauth2_oidc = OpenIdConnect(
    openIdConnectUrl=str(config.oidc.discovery_endpoint),
    scheme_name=config.oidc.PROVIDER_NAME,
)


async def current_user(
    request: Request, token: Optional[str] = Security(fastapi_oauth2_oidc)
):
    # we could query the identity provider to give us some information about the user
    # userinfo = await self.authlib_oauth.myapp.userinfo(token={"access_token": token})

    # in my case, the JWT already contains all the information so I only need to decode and verify it
    try:
        # note that this also validates the JWT by validating all the claims
        log.info(f'#######"id_token": {token}')
        user = await authlib_oauth_app.parse_id_token(
            request, token={"id_token": token}
        )
    except Exception as exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Supplied authentication could not be validated ({exp})",
        )
    return user


@app.get("/")
async def login(request: Request):
    log.info("TEST INFO LOG")
    log.debug("TEST DEBUG LOG")
    log.error("TEST ERROR LOG")
    return "hello world"


@app.get("/locked")
async def only_for_logged_in_users_test(user=Security(current_user, scopes=["openid"])):
    return f"hello authorized user {user}"


@app.get("/login")
async def login(request: Request):
    #log.debug(request.session)
    #request.session['test'] = 'foo'
    redirect_uri = request.url_for("auth")
    log.debug(f"/login redirect_uri:{redirect_uri}")

    return await authlib_oauth_app.authorize_redirect(request, str(redirect_uri))


@app.get(
    "/auth",
    #response_model=JWTTokenResponse,
    responses={401: {"model": OAuthErrorHTTPResponse}},
    response_description="a OAuth2Token token to be used to authenticate against the API",
)
async def auth(request: Request):
    
    #log.debug(request.session.get('test', ''))
    try:
        # We use the OAuth2 Authorization Code Flow. That means the OIDC provider send the auth code to here.
        # we create the refresh and access token from the auth code and send the access token back to the user
        print(request.session)
        user_oauth_token: OAuth2Token = await authlib_oauth_app.authorize_access_token(
            request
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

    assert userinfo[config.oidc.user_id_attribute], "User ID attribute is empty"
    client_access_token = JWTTokenContainer(
        sub=userinfo[config.oidc.user_id_attribute],
        scope=userinfo[config.oidc.user_group_attribute],
    )

    # user = token["userinfo"]
    return client_access_token.get_response()


@app.get("/me")
def me(user=Depends(current_user)):
    return user
