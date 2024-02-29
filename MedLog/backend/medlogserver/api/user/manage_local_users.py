from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List

from fastapi import Depends, Security, FastAPI, HTTPException, status, Query, Body, Form
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter
from medlogserver.api.paginator import pagination_query, PageParams, PaginatedResponse

from medlogserver.db.user.crud import (
    User,
    UserCRUD,
    UserCreate,
    UserUpdate,
    UserUpdateByUser,
    UserUpdateByAdmin,
)
from medlogserver.db.user_auth.crud import (
    UserAuth,
    UserAuthCreate,
    UserAuthUpdate,
    UserAuthCRUD,
    AllowedAuthSourceTypes,
)
from medlogserver.api.auth.base import (
    TOKEN_ENDPOINT_PATH,
    oauth2_scheme,
    user_is_admin,
    user_is_usermanager,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
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


fast_api_user_manage_router: APIRouter = APIRouter()


@fast_api_user_manage_router.post(
    "/user",
    response_model=User,
    name="Create local user",
    description=f"Creates a new user in the local user database. {NEEDS_USERMAN_API_INFO}",
)
async def create_user(
    user_create: UserCreate,
    user_password: Annotated[
        str,
        Query(
            description="The password for the created user. If non is defined the user will be created but not able to login until an admin user defines a password.",
        ),
    ] = None,
    current_user_is_usermanager: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> User:
    wrong_login_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect user_name or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not current_user_is_usermanager:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing role",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_create: User = await user_crud.create(
        user_create,
        raise_custom_exception_if_exists=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User allready exists",
            headers={"WWW-Authenticate": "Bearer"},
        ),
    )
    if user_password:
        user_auth: UserAuth = await user_auth_crud.create(
            UserAuthCreate(
                auth_source_type=AllowedAuthSourceTypes.local, password=user_password
            )
        )
    return user_create


@fast_api_user_manage_router.get(
    "/user",
    response_model=PaginatedResponse[User],
    description=f"Get account data from a user by its id.  {NEEDS_USERMAN_API_INFO}",
)
async def list_users(
    incl_deactivated: bool = Query(
        default=False, description="Also list deactivated users."
    ),
    is_user_manager: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    pagination: PageParams = Depends(pagination_query),
) -> PaginatedResponse[User]:
    users = await user_crud.list(show_deactivated=incl_deactivated)
    return PaginatedResponse(
        total_count=await user_crud.count(
            show_deactivated=incl_deactivated,
        ),
        offset=pagination.offset,
        count=len(users),
        items=users,
    )


@fast_api_user_manage_router.get(
    "/user/me",
    response_model=User,
    description="Get account data from the current user",
)
async def get_myself(
    current_user: UserAuthCRUD = Depends(get_current_user),
) -> User:
    return current_user


@fast_api_user_manage_router.patch(
    "/user/me",
    response_model=User,
    description="Update my user account data.",
)
async def update_myself(
    patched_user: UserUpdateByUser,
    current_user: User = Security(get_current_user),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.update(patched_user, user_id=current_user.id)


@fast_api_user_manage_router.put(
    "/user/me/password",
    response_model=User,
    description="Set my password if i am a 'local' user. If my account was provisioned via an external OpenID Connect provider this does nothing except the return value will be `false`.",
)
async def set_my_password(
    old_password: str = Form(default=None),
    new_password: str = Form(default=None),
    new_password_repeated: str = Form(
        default=None,
        description="For good measure we require the password twice to mitiage typos.",
    ),
    current_user: User = Security(get_current_user),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> bool:
    if new_password != new_password_repeated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new password and repeated new password do not match",
        )

    old_user_auth: UserAuth = await user_auth_crud.get_local_auth_source_by_user_id(
        current_user.id
    )
    if old_user_auth is None:
        return False
    old_user_auth.verify_password(
        old_password,
        raise_exception_if_wrong_pw=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify authorization",
        ),
    )
    updated_user_auth = UserAuthUpdate(password=new_password)
    await user_auth_crud.update(updated_user_auth, id=old_user_auth.id)
    return True


@fast_api_user_manage_router.get(
    "/user/{user_id}",
    response_model=User,
    description=f"Get account data from a user by its id. {NEEDS_USERMAN_API_INFO}",
)
async def get_user(
    user_id: str,
    current_user: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.get(user_id)


@fast_api_user_manage_router.patch(
    "/user/{user_id}",
    response_model=User,
    description=f"Get account data from a user by its id. {NEEDS_USERMAN_API_INFO}",
)
async def update_user(
    user_id: str,
    patched_user: Annotated[
        UserUpdateByAdmin, Body(description="The user object with changed data")
    ],
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.update(user_id, patched_user)


@fast_api_user_manage_router.put(
    "/user/{user_id}/password",
    response_model=User,
    description=f"Set a local users password. If the user is provisioned via an external OpenID Connect provider this does nothing except the return value will be `false`.  {NEEDS_USERMAN_API_INFO}",
)
async def set_user_password(
    user_id: str,
    new_password: str = Form(default=None),
    new_password_repeated: str = Form(
        default=None,
        description="For good measure we require the password twice to mitiage typos.",
    ),
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> bool:
    if new_password != new_password_repeated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new password and repeated new password do not match",
        )
    old_user_auth = user_auth_crud.get_local_auth_source_by_user_id(user_id)
    if old_user_auth is None:
        return False
    updated_user_auth = UserAuthUpdate(password=new_password)
    await user_auth_crud.update(updated_user_auth)
    return True
