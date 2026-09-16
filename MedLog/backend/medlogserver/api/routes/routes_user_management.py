from typing import Annotated, Sequence, List, Type
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import (
    Depends,
    Security,
    FastAPI,
    HTTPException,
    status,
    Query,
    Body,
    Form,
    Response,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.model.user_role import UserRoleApiRead
from medlogserver.db.user import (
    User,
    UserCRUD,
    UserCreate,
    UserUpdate,
    UserUpdateByUser,
    UserUpdateByAdmin,
)
from medlogserver.db.user_auth import (
    UserAuth,
    UserAuthCreate,
    UserAuthUpdate,
    UserAuthCRUD,
    AllowedAuthSchemeType,
)
from medlogserver.api.auth.security import (
    user_is_admin,
    user_is_usermanager,
    get_current_user,
)
from medlogserver.api.auth.security import (
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)
from medlogserver.model.api_only.api_token import ApiTokenRead


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
    user_create: Annotated[
        UserCreate, Body(description="A json body with the user details")
    ],
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing role",
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
                user_id=user_create.id,
                auth_source_type=AllowedAuthSchemeType.basic,
                basic_password=user_password,
            )
        )
    return user_create


UserQueryParams: Type[QueryParamsInterface] = create_query_params_class(User)


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
    pagination: QueryParamsInterface = Depends(UserQueryParams),
) -> PaginatedResponse[User]:
    if not is_user_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Needs usermanager role"
        )
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
    "/user/{user_id}",
    response_model=User,
    description=f"Get account data from a user by its id. {NEEDS_USERMAN_API_INFO}",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.get(
        user_id,
        show_deactivated=True,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ),
    )


@fast_api_user_manage_router.patch(
    "/user/{user_id}",
    response_model=User,
    description=f"Get account data from a user by its id. {NEEDS_USERMAN_API_INFO}",
)
async def update_user(
    user_id: uuid.UUID,
    patched_user: Annotated[
        UserUpdateByAdmin, Body(description="The user object with changed data")
    ],
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.update(user_update=patched_user, user_id=user_id)


@fast_api_user_manage_router.put(
    "/user/{user_id}/password",
    response_model=User,
    description=f"Set a local users password. If the user is provisioned via an external OpenID Connect provider the user will now be able to also login with basic login with this password.  {NEEDS_USERMAN_API_INFO}",
)
async def set_user_password(
    user_id: uuid.UUID,
    new_password: str = Form(),
    new_password_repeated: str = Form(
        description="For good measure we require the password twice to mitiage typos.",
    ),
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> bool:
    if new_password != new_password_repeated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new password and repeated new password do not match",
        )
    user = await user_crud.get(
        user_id=user_id,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ),
    )
    user_auth_pw = await user_auth_crud.get_basic_auth_source_by_user_id(user_id)

    if user_auth_pw is None:
        log.debug(f"First time set pw for user '{user.user_name}' {new_password}")
        # lets create a userAuth with the new password
        user_auth_create = UserAuthCreate(
            user_id=user_id,
            auth_source_type=AllowedAuthSchemeType.basic,
            basic_password=new_password,
        )
        user_auth_pw: UserAuth = await user_auth_crud.create(user_auth_create)
    else:
        user_auth_update = UserAuthUpdate(basic_password=new_password)
        user_auth_pw = await user_auth_crud.update(
            user_auth_update=user_auth_update, id_=user_auth_pw.id
        )
    return user


@fast_api_user_manage_router.get(
    "/role",
    response_model=List[UserRoleApiRead],
    name="Get Roles",
    description=f"List available roles",
)
async def create_user(
    current_user: bool = Security(get_current_user),
) -> List[UserRoleApiRead]:
    return [
        UserRoleApiRead(
            role_name=config.ADMIN_ROLE_NAME,
            description="The admin role enables the user to access and edit all studies.",
            has_admin_permissions=True,
            has_usermanager_permissions=True,
        ),
        UserRoleApiRead(
            role_name=config.USERMANAGER_ROLE_NAME,
            description="The user manager role allows a user to edit all user allocation for all studies.",
            has_admin_permissions=False,
            has_usermanager_permissions=True,
        ),
    ]


# Available regardless of API_TOKEN_MANAGEMENT_ENABLED, so a user manager can still clean
# up after the feature was switched off.
@fast_api_user_manage_router.get(
    "/user/{user_id}/api-token",
    response_model=List[ApiTokenRead],
    description=f"List the API tokens of a user, newest first. The secret part of a token can not be recalled. {NEEDS_USERMAN_API_INFO}",
)
async def list_api_tokens_of_user(
    user_id: uuid.UUID,
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> List[ApiTokenRead]:
    await user_crud.get(
        user_id,
        show_deactivated=True,
        raise_exception_if_none=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ),
    )
    tokens = await user_auth_crud.list_api_tokens_by_user_id(user_id)
    return [ApiTokenRead.from_user_auth(token) for token in tokens]


@fast_api_user_manage_router.delete(
    "/user/{user_id}/api-token/{api_token_id}",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    description=f"Revoke an API token of a user, e.g. when it leaked. It stops working immediately. {NEEDS_USERMAN_API_INFO}",
)
async def revoke_api_token_of_user(
    user_id: uuid.UUID,
    api_token_id: uuid.UUID,
    current_user_is_user_manager: bool = Security(user_is_usermanager),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
):
    token = await user_auth_crud.get_api_token_of_user(user_id, api_token_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API token not found.",
        )
    await user_auth_crud.delete(token.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
