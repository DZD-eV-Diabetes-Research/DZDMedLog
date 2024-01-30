from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.REST_api.auth.jwt import JWTTokenResponse, JWTTokenContainer
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
from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
fast_api_local_auth_router: APIRouter = APIRouter()


@fast_api_local_auth_router.post("/token", response_model=JWTTokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_crud: UserCRUD = Depends(get_users_crud),
    user_auth_crud: UserAuthCRUD = Depends(get_user_auth_crud),
    user_auth_access_token_crud: UserAuthAccessTokenCRUD = Depends(
        get_user_auth_access_token_crud
    ),
) -> JWTTokenResponse:
    wrong_login_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # find user auth data
    user_auth: UserAuth = await user_auth_crud.get_local_auth_source_by_username(
        username=form_data.username, raise_exception_if_none=wrong_login_exception
    )
    # verifiy users pw
    user_auth.verify_password(
        form_data.password, raise_exception_if_wrong_pw=wrong_login_exception
    )
    # get full user data. HINT: user can exist but maybe disabled, thats why the `raise_exception_if_none`
    user: User = await user_crud.get(
        user_auth.user_id, raise_exception_if_none=wrong_login_exception
    )
    # create access token
    access_token = JWTTokenContainer(user=user)
    if config.AUTH_CHECK_TOKENS_FOR_REVOKATION:
        await user_auth_access_token_crud.create(
            UserAuthAccessTokenCreate(
                user_auth_id=user_auth.id,
                token_encoded=access_token.jwt_token_encoded,
                valid_until_timestamp=int(access_token.exp),
            )
        )
    return access_token.get_response()
