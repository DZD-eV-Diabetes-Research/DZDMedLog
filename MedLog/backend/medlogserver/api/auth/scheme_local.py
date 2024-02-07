from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, HTTPException, status, Query, Body
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.api.auth.tokens import (
    JWTBundleTokenResponse,
    JWTAccessTokenContainer,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.user import get_user_crud, User, UserCRUD, UserCreate
from medlogserver.db.user.user_auth import (
    get_user_auth_crud,
    UserAuth,
    UserAuthCreate,
    UserAuthCRUD,
    UserAuthRefreshToken,
    UserAuthRefreshTokenCreate,
    UserAuthRefreshTokenCRUD,
    get_user_auth_refresh_token_crud,
    AllowedAuthSourceTypes,
)
from medlogserver.api.auth.base import (
    TOKEN_ENDPOINT_PATH,
    oauth2_scheme,
    user_is_admin,
    user_is_usermanager,
)

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)
from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_auth_local_router: APIRouter = APIRouter()


@fast_api_auth_local_router.post(
    TOKEN_ENDPOINT_PATH,
    response_model=JWTBundleTokenResponse,
    name="Login for refresh and access token",
)
async def login_for_token_set(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_crud: UserCRUD = Depends(get_user_crud),
    user_auth_crud: UserAuthCRUD = Depends(get_user_auth_crud),
    user_auth_access_token_crud: UserAuthRefreshTokenCRUD = Depends(
        get_user_auth_refresh_token_crud
    ),
) -> JWTBundleTokenResponse:
    wrong_login_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect user_name or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # find user auth data
    user_auth: UserAuth = await user_auth_crud.get_local_auth_source_by_user_name(
        user_name=form_data.username, raise_exception_if_none=wrong_login_exception
    )
    # verifiy users pw
    user_auth.verify_password(
        form_data.password, raise_exception_if_wrong_pw=wrong_login_exception
    )
    # get full user data. HINT: user can exist but maybe deactivated, thats why the `raise_exception_if_none`
    user: User = await user_crud.get(
        user_auth.user_id, raise_exception_if_none=wrong_login_exception
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
