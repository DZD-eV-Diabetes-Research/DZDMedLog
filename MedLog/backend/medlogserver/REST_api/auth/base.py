from pydantic import BaseModel, Field


from datetime import datetime, timedelta, timezone
from typing import List, Literal, Annotated
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import HTTPException, status, Security, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

#
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.user import User, ClientAccessToken
from medlogserver.REST_api.auth.jwt import JWTTokenContainer
from medlogserver.db.user import get_users_crud, UserCRUD, User
from medlogserver.db.user_auth import (
    get_user_auth_crud,
    UserAuthCRUD,
    UserAuth,
    get_user_auth_access_token_crud,
    UserAuthAccessTokenCRUD,
    UserAuthAccessToken,
)

log = get_logger()
config = Config()


TOKEN_ENDPOINT = "token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_ENDPOINT)


async def get_current_user(
    token: Annotated[str, Security(oauth2_scheme)],
    user_auth_access_token_crud: UserAuthAccessTokenCRUD = Depends(
        get_user_auth_access_token_crud
    ),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt: JWTTokenContainer = JWTTokenContainer.from_existing_encoded_jwt(token)
        if jwt.user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if config.AUTH_CHECK_TOKENS_FOR_REVOKATION:
        access_token_from_db = None
        if jwt.id is None:
            user_auth_access_tokens = await user_auth_access_token_crud.list_by_user(
                user_id=jwt.user_id
            )
            for token in user_auth_access_tokens:
                if token.token_encoded == jwt.jwt_token:
                    access_token_from_db = token
                    break
        else:
            access_token_from_db = await user_auth_access_token_crud.get(id=jwt.id)
        if access_token_from_db is None or access_token_from_db.disabled:
            raise credentials_exception
    if jwt.is_expired():
        raise credentials_exception
    # YOU ARE HERE. EXTARCT USER INFO FROM TOKEN AND BUILD USER OBJECT AND RETURN
    user = None
    if user is None:
        raise credentials_exception
    return user
