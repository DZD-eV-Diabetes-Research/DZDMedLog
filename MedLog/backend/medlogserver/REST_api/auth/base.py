from pydantic import BaseModel, Field


from datetime import datetime, timedelta, timezone
from typing import List, Literal, Annotated
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import HTTPException, status, Security, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

#
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.REST_api.auth.tokens import (
    JWTAccessTokenContainer,
    JWTAccessTokenResponse,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user import get_users_crud, UserCRUD, User
from medlogserver.db.user_auth import (
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


TOKEN_ENDPOINT_PATH = "/token"
fast_api_auth_base_router: APIRouter = APIRouter()


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
            show_disabled=False,
            raise_exception_if_none=credentials_exception,
        )
    return access_jwt.user


async def user_is_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> bool:
    if config.ADMIN_ROLE_NAME in user.roles:
        return True
    return False


async def user_is_usermanager(
    user: Annotated[User, Depends(get_current_user)],
) -> bool:
    if (
        config.USERMANAGER_ROLE_NAME in user.roles
        or config.ADMIN_ROLE_NAME in user.roles
    ):
        return True
    return False


@fast_api_auth_base_router.post("/refresh", response_model=JWTAccessTokenResponse)
async def get_fresh_access_token(
    refresh_token: str,
    current_user_is_usermanager: bool = Depends(user_is_usermanager),
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
    r_token = JWTRefreshTokenContainer.from_existing_jwt(refresh_token)
    if r_token.is_expired():
        raise token_invalid_exception

    # this will raise error if token is deleted or disabled (aka. revoked).
    r_token_from_db = await user_auth_refresh_token_crud.get(
        r_token.id, show_disabled=False, raise_exception_if_none=token_invalid_exception
    )
    user = await user_crud.get(r_token.user_id)
    if user.disabled:
        token_invalid_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    fresh_access_token = JWTAccessTokenContainer(
        user=user, parent_refresh_token_id=r_token.id
    )
    return fresh_access_token
