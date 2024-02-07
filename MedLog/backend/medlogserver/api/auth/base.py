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
from medlogserver.api.auth.tokens import (
    JWTAccessTokenContainer,
    JWTAccessTokenResponse,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.user import get_user_crud, UserCRUD, User
from medlogserver.db.user.user_auth import (
    get_user_auth_crud,
    UserAuthCRUD,
    UserAuth,
    UserAuthCreate,
    get_user_auth_refresh_token_crud,
    UserAuthRefreshTokenCRUD,
    UserAuthRefreshToken,
    AllowedAuthSourceTypes,
)

log = get_logger()
config = Config()


TOKEN_ENDPOINT_PATH = "/auth/token"
REFRESH_ACCESS_TOKEN_ENDPOINT_PATH = "/auth/refresh"
fast_api_auth_base_router: APIRouter = APIRouter()

NEEDS_ADMIN_API_INFO = "Needs admin role."
NEEDS_USERMAN_API_INFO = "Needs admin or user-manager role."

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_ENDPOINT_PATH)


async def get_current_user(
    token: Annotated[str, Security(oauth2_scheme)],
    user_auth_refresh_token_crud: UserAuthRefreshTokenCRUD = Depends(
        get_user_auth_refresh_token_crud
    ),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # extract user data from access token.
    # no database interaction needed (if config.AUTH_CHECK_REFRESH_TOKENS_FOR_REVOKATION is set to False)
    try:
        access_jwt: JWTAccessTokenContainer = JWTAccessTokenContainer.from_existing_jwt(
            token
        )
        if access_jwt.user is None or access_jwt.is_expired():
            raise credentials_exception
        if access_jwt.is_expired():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise credentials_exception

    if config.AUTH_CHECK_REFRESH_TOKENS_FOR_REVOKATION:
        parent_refresh_token = await user_auth_refresh_token_crud.get(
            access_jwt.parent_refresh_token_id,
            show_deactivated=False,
            raise_exception_if_none=credentials_exception,
        )
    return access_jwt.user


async def user_is_admin(
    user: Annotated[User, Security(get_current_user)],
) -> bool:
    if not config.ADMIN_ROLE_NAME in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not admin",
        )
        return False
    return True


async def user_is_usermanager(
    user: Annotated[User, Security(get_current_user)],
) -> bool:
    if not (
        config.USERMANAGER_ROLE_NAME in user.roles
        or config.ADMIN_ROLE_NAME in user.roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not user manager",
        )
        return False
    return True


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
    user_crud: UserCRUD = Depends(get_user_auth_crud),
    user_auth_crud: UserAuthCRUD = Depends(get_user_auth_crud),
    user_auth_refresh_token_crud: UserAuthRefreshTokenCRUD = Depends(
        get_user_auth_refresh_token_crud
    ),
) -> User:
    token_invalid_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token not valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    refresh_token: str = None
    if refresh_token_form:
        refresh_token = refresh_token_form
    elif refresh_token_header:
        refresh_token = refresh_token_header
    else:
        raise token_invalid_exception
    if refresh_token.lower().startswith("bearer"):
        token_type, refresh_token = refresh_token_header.split(" ")

    r_token = JWTRefreshTokenContainer.from_existing_jwt(refresh_token)
    if r_token.is_expired():
        raise token_invalid_exception

    # this will raise error if token is deleted or deactivated (aka. revoked).
    r_token_from_db = await user_auth_refresh_token_crud.get(
        r_token.id,
        show_deactivated=False,
        raise_exception_if_none=token_invalid_exception,
    )
    user = await user_crud.get(r_token.user_id)
    if user.deactivated:
        token_invalid_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    fresh_access_token = JWTAccessTokenContainer(
        user=user, parent_refresh_token_id=r_token.id
    )
    return fresh_access_token
