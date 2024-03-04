from pydantic import BaseModel, Field


from datetime import datetime, timedelta, timezone
from typing import List, Literal, Annotated, NoReturn
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import (
    HTTPException,
    status,
    Security,
    Depends,
    APIRouter,
    Form,
    Header,
    Query,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    OAuth2AuthorizationCodeBearer,
    OpenIdConnect,
)

#
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.api.auth.model_token import (
    JWTAccessTokenContainer,
    JWTAccessTokenResponse,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.crud import UserCRUD, User
from medlogserver.db.user_auth.crud import UserAuthCRUD
from medlogserver.db.user_auth_refresh_token.crud import UserAuthRefreshTokenCRUD

log = get_logger()
config = Config()


TOKEN_ENDPOINT_PATH = "/auth/token"
REFRESH_ACCESS_TOKEN_ENDPOINT_PATH = "/auth/refresh"
fast_api_auth_base_router: APIRouter = APIRouter()

NEEDS_ADMIN_API_INFO = "Needs admin role."
NEEDS_USERMAN_API_INFO = "Needs admin or user-manager role."

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_ENDPOINT_PATH)


@fast_api_auth_base_router.post(
    REFRESH_ACCESS_TOKEN_ENDPOINT_PATH,
    response_model=JWTAccessTokenResponse,
    description="Endpoint to get a new/fresh access token. A valid refresh token must be provided. Accepts the refresh token either as a form field **OR** in the 'refresh-token' header field.<br>Returns a new access token on success.",
)
async def get_fresh_access_token(
    refresh_token_form: str = Form(default=None),
    refresh_token_header: str = Header(
        default=None,
        alias="refresh-token",
        example="Bearer S0VLU0UhIExFQ0tFUiEK",
        description="Refresh token via `refresh-token` header field",
    ),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_auth_refresh_token_crud: UserAuthRefreshTokenCRUD = Depends(
        UserAuthRefreshTokenCRUD.get_crud
    ),
) -> User:
    token_invalid_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token not valid2",
        headers={"WWW-Authenticate": "Bearer"},
    )
    refresh_token: str = None

    if refresh_token_form:
        refresh_token = refresh_token_form
    elif refresh_token_header:
        refresh_token = refresh_token_header
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not valid. Can not find",
            headers={"WWW-Authenticate": "Bearer"},
        )
    log.debug(
        f"Access '{REFRESH_ACCESS_TOKEN_ENDPOINT_PATH}' with token ('refresh_token'):' {refresh_token}'"
    )
    if refresh_token.lower().startswith("bearer"):
        token_type, refresh_token = refresh_token_header.split(" ")

    r_token = JWTRefreshTokenContainer.from_existing_jwt(refresh_token)
    """
    # this will raise error if token is deleted or deactivated (aka. revoked).
    # ToDO: not implented yet. we need to save the refresh token first
    r_token_from_db = await user_auth_refresh_token_crud.get(
        r_token.id,
        show_deactivated=False,
        raise_exception_if_none=token_invalid_exception,
    )
    """

    user = await user_crud.get(r_token.user_id)
    if user.deactivated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not valid. User deactivted",
            headers={"WWW-Authenticate": "Bearer"},
        )

    fresh_access_token = JWTAccessTokenContainer(
        user=user, parent_refresh_token_id=r_token.id
    )
    return fresh_access_token.to_token_response()
