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
        access_jwt: JWTTokenContainer = JWTTokenContainer.from_existing_encoded_jwt(
            token
        )
        if access_jwt.user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    if config.AUTH_CHECK_TOKENS_FOR_REVOKATION:
        access_token_from_db = None

        if access_jwt.id is None:
            stored_user_auth_access_tokens = (
                await user_auth_access_token_crud.list_by_user(
                    user_id=access_jwt.user.id
                )
            )

            for stored_user_access_token in stored_user_auth_access_tokens:
                if stored_user_access_token.token_encoded == access_jwt.jwt_token:
                    access_token_from_db = stored_user_access_token
                    break
        else:
            access_token_from_db = await user_auth_access_token_crud.get(
                id=access_jwt.id
            )
        if access_token_from_db is None or access_token_from_db.disabled:
            raise credentials_exception
    if access_jwt.is_expired():
        raise credentials_exception
    return access_jwt.user
