import logging

from fastapi import FastAPI
from fastapi.security.open_id_connect_url import OpenIdConnect
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException
from fastapi import Request
from fastapi import Depends
from fastapi import status
from typing import Optional


# internal imports
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
log.info("GET CONFIG")
config = Config()


app = FastAPI(
    swagger_ui_init_oauth={
        "clientId": config.oidc.client_id,
        "appName": "medlog",
        "usePkceWithAuthorizationCodeGrant": False,
        "scopes": "openid profile email",
    }
)
app.add_middleware(SessionMiddleware, secret_key=config.oidc.jwt_secret)
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

authlib_oauth_app = authlib_oauth.medlog

fastapi_oauth2 = OpenIdConnect(
    openIdConnectUrl=str(config.oidc.discovery_endpoint),
    scheme_name=config.oidc.PROVIDER_NAME,
)


async def current_user(
    request: Request, token: Optional[str] = Depends(fastapi_oauth2)
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


@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    log.debug(f"/login redirect_uri:{redirect_uri}")

    return await authlib_oauth_app.authorize_redirect(request, str(redirect_uri))


@app.get("/auth")
async def auth(request: Request):
    token = await authlib_oauth_app.authorize_access_token(request)
    # <=0.15
    # user = await oauth.google.parse_id_token(request, token)
    userinfo = await authlib_oauth_app.userinfo(
        token={"access_token": token["access_token"]}
    )
    # user = token["userinfo"]
    return {"USER": userinfo, "TOKEN": token}


@app.get("/me")
def me(user=Depends(current_user)):
    return user
