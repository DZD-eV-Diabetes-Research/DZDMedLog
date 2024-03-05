from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, HTTPException, status, Query, Body
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.api.auth.model_token import (
    JWTBundleTokenResponse,
    JWTAccessTokenContainer,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user import User, UserCRUD, UserCreate
from medlogserver.db.user_auth import (
    UserAuth,
    UserAuthCRUD,
)
from medlogserver.model.user_auth_refresh_token import UserAuthRefreshTokenCreate
from medlogserver.db.user_auth_refresh_token import UserAuthRefreshTokenCRUD
from medlogserver.api.routes.routes_auth import TOKEN_ENDPOINT_PATH


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
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_auth_access_token_crud: UserAuthRefreshTokenCRUD = Depends(
        UserAuthRefreshTokenCRUD.get_crud
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
