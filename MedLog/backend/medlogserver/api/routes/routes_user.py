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
    get_current_user_by_session,
)
from medlogserver.model.api_only.api_token import (
    ApiTokenCreate,
    ApiTokenRead,
    ApiTokenCreated,
)


from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_user_self_service_router: APIRouter = APIRouter()


@fast_api_user_self_service_router.get(
    "/user/me",
    response_model=User,
    description="Get account data from the current user",
)
async def get_myself(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@fast_api_user_self_service_router.patch(
    "/user/me",
    response_model=User,
    description="Update my user account data.",
)
async def update_myself(
    patched_user: UserUpdateByUser,
    current_user: User = Security(get_current_user),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
) -> User:
    return await user_crud.update(user_update=patched_user, user_id=current_user.id)


@fast_api_user_self_service_router.put(
    "/user/me/password",
    response_model=bool,
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

    old_user_auth: UserAuth = await user_auth_crud.get_basic_auth_source_by_user_id(
        current_user.id
    )
    if old_user_auth is None:
        return False
    old_user_auth.verify_password(
        old_password,
        raise_exception_if_wrong=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify authorization",
        ),
    )
    updated_user_auth = UserAuthUpdate(basic_password=new_password)
    await user_auth_crud.update(updated_user_auth, id_=old_user_auth.id)
    return True


API_TOKEN_MANAGEMENT_API_INFO = (
    "Needs `API_TOKEN_MANAGEMENT_ENABLED` and a browser session login, "
    "API tokens can not manage API tokens. See `/api/config/api-token`."
)


def _raise_if_api_token_management_disabled():
    if not config.API_TOKEN_MANAGEMENT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API token management is disabled on this server.",
        )


@fast_api_user_self_service_router.get(
    "/user/me/api-token",
    response_model=List[ApiTokenRead],
    description=f"List my API tokens, newest first. The secret part of a token can not be recalled. {API_TOKEN_MANAGEMENT_API_INFO}",
)
async def list_my_api_tokens(
    current_user: User = Security(get_current_user_by_session),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> List[ApiTokenRead]:
    _raise_if_api_token_management_disabled()
    tokens = await user_auth_crud.list_api_tokens_by_user_id(current_user.id)
    return [ApiTokenRead.from_user_auth(token) for token in tokens]


@fast_api_user_self_service_router.post(
    "/user/me/api-token",
    response_model=ApiTokenCreated,
    status_code=status.HTTP_201_CREATED,
    description=(
        "Create a new API token for my account. The response contains the complete token, "
        "it is shown only once. The token is bound to my account, not to my current login, "
        "so it keeps working after logout until it expires or gets revoked. "
        "Answers 409 if the user already has `max_tokens_per_user` unexpired tokens. "
        f"{API_TOKEN_MANAGEMENT_API_INFO}"
    ),
)
async def create_my_api_token(
    token_create: ApiTokenCreate,
    current_user: User = Security(get_current_user_by_session),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
) -> ApiTokenCreated:
    _raise_if_api_token_management_disabled()
    max_tokens = config.API_TOKEN_MANAGEMENT_MAX_TOKENS_PER_USER
    if (
        max_tokens is not None
        and await user_auth_crud.count_unexpired_managed_api_tokens(current_user.id)
        >= max_tokens
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have {max_tokens} API tokens, which is the maximum. Revoke one you no longer need first.",
        )
    max_days = config.API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS
    if "expires_in_days" in token_create.model_fields_set:
        expires_in_days = token_create.expires_in_days
    else:
        expires_in_days = config.API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS
    if max_days is not None and expires_in_days is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tokens without expiry are not allowed. `expires_in_days` must be between 1 and {max_days}.",
        )
    if max_days is not None and expires_in_days > max_days:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"`expires_in_days` must not exceed {max_days}.",
        )
    expires_at_epoch_time = None
    if expires_in_days is not None:
        expires_at_epoch_time = int(
            (datetime.now(tz=timezone.utc) + timedelta(days=expires_in_days)).timestamp()
        )
    user_auth_token = UserAuthCreate(
        user_id=current_user.id,
        auth_source_type=AllowedAuthSchemeType.api_token,
        api_token_name=token_create.name,
        # no source login: the token is bound to the user and survives logout
        api_token_source_user_auth_id=None,
        expires_at_epoch_time=expires_at_epoch_time,
    )
    user_auth_token.generate_api_token()
    plain_token = user_auth_token.get_api_token()
    # the token gets hashed when written into the DB, the plain token is gone after this response
    user_auth = await user_auth_crud.create(user_auth_token)
    return ApiTokenCreated(
        **ApiTokenRead.from_user_auth(user_auth).model_dump(exclude={"expired"}),
        token=plain_token,
    )


@fast_api_user_self_service_router.delete(
    "/user/me/api-token/{api_token_id}",
    response_class=Response,
    status_code=status.HTTP_204_NO_CONTENT,
    description=f"Revoke one of my API tokens. It stops working immediately. {API_TOKEN_MANAGEMENT_API_INFO}",
)
async def revoke_my_api_token(
    api_token_id: uuid.UUID,
    current_user: User = Security(get_current_user_by_session),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
):
    _raise_if_api_token_management_disabled()
    token = await user_auth_crud.get_api_token_of_user(current_user.id, api_token_id)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API token not found.",
        )
    await user_auth_crud.delete(token.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
