from typing import Optional


from typing import List, Literal, Annotated, NoReturn
import datetime
import uuid

from fastapi import (
    HTTPException,
    status,
    Security,
    Depends,
    APIRouter,
    Form,
    Header,
    Query,
    Request,
)

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    OAuth2AuthorizationCodeBearer,
    OpenIdConnect,
)


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

#
from medlogserver.utils import slugify_string
from medlogserver.db.user import UserCRUD, User
from medlogserver.db.user_auth import (
    UserAuthCRUD,
    UserAuth,
    AllowedAuthSchemeType,
    UserAuthUpdate,
)
from medlogserver.db.user_session import UserSessionCRUD, UserSession
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.api.auth.utils import (
    oidc_refresh_access_token,
    register_and_create_oauth_clients,
    validate_api_token,
    wipe_expired_user_session_or_user_auth,
    OAuthContainer,
)

log = get_logger()
config = Config()


oauth_clients: dict[str, OAuthContainer] = register_and_create_oauth_clients()

SESSION_COOKIE_NAME = f"session_{slugify_string(config.APP_NAME, '_')}"
NEEDS_ADMIN_API_INFO = "Needs Admin role"
NEEDS_USERMAN_API_INFO = "Need usermanager role"
api_token_security = HTTPBearer(auto_error=False)
not_authenticated_exception = HTTPException(status_code=401, detail="Not authenticated")


async def get_current_user_auth(
    request: Request,
    user_session_crud: UserSessionCRUD = Depends(UserSessionCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    api_token: Optional[HTTPAuthorizationCredentials] = Depends(api_token_security),
) -> UserAuth:
    user_auth: UserAuth | None = None
    user_session: UserSession | None = None
    if api_token:
        # api tokens are not session based
        token = api_token.credentials
        user_auth_token: UserAuth = await validate_api_token(
            token=token,
            not_authenticated_exception=not_authenticated_exception,
            user_auth_crud=user_auth_crud,
        )
        # santiy check
        assert user_auth_token.auth_source_type == AllowedAuthSchemeType.api_token
        user_auth = user_auth_token
        if user_auth_token.is_managed_api_token:
            if not config.API_TOKEN_MANAGEMENT_ENABLED:
                # Disabling the feature must also lock out the tokens created while it was on.
                log.debug("Token management is disabled, rejecting managed api token")
                raise not_authenticated_exception
        else:
            user_auth = await user_auth_crud.get(
                user_auth_token.api_token_source_user_auth_id
            )
            if user_auth is None:
                # the login the token was derived from is gone (logout or token cleaner)
                raise not_authenticated_exception

    else:
        # if not token based auth then it must be a session
        session_id = request.cookies.get(SESSION_COOKIE_NAME, None)
        if not session_id:
            raise not_authenticated_exception
        session_id = uuid.UUID(session_id)
        user_session: UserSession = await user_session_crud.get(session_id)
        if not user_session:
            raise not_authenticated_exception
        user_auth = await user_auth_crud.get(user_session.user_auth_id)
    if (
        user_session is not None and user_session.is_expired()
    ) or user_auth.is_expired():
        if user_auth.revoked:
            raise not_authenticated_exception
        if user_auth.auth_source_type == AllowedAuthSchemeType.basic:
            await wipe_expired_user_session_or_user_auth(
                user_auth=user_auth,
                user_auth_crud=user_auth_crud,
                user_session=user_session,
                user_session_crud=user_session_crud,
            )
            raise not_authenticated_exception
        elif user_auth.auth_source_type == AllowedAuthSchemeType.oidc:
            if user_session is None:
                # Expired OIDC auth reached via API token — no browser session to refresh through
                raise not_authenticated_exception
            try:
                user_auth = await oidc_refresh_access_token(
                    oauth_client=oauth_clients[user_auth.oidc_provider_slug],
                    user_auth_crud=user_auth_crud,
                    user_auth=user_auth,
                    user_session_crud=user_session_crud,
                    user_session=user_session,
                    raise_custom_expection_if_fails=not_authenticated_exception,
                )
            except HTTPException as e:
                await wipe_expired_user_session_or_user_auth(
                    user_auth=user_auth,
                    user_auth_crud=user_auth_crud,
                    user_session=user_session,
                    user_session_crud=user_session_crud,
                )
                raise e
    return user_auth


async def get_logged_in_state(
    request: Request,
    user_session_crud: UserSessionCRUD = Depends(UserSessionCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    api_token: Optional[HTTPAuthorizationCredentials] = Depends(api_token_security),
) -> bool:
    try:
        user_auth: UserAuth | None = await get_current_user_auth(
            request=request,
            user_session_crud=user_session_crud,
            user_auth_crud=user_auth_crud,
            api_token=api_token,
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return False
    if user_auth is not None:
        return True

    return False


async def get_current_user(
    request: Request,
    user_session_crud: UserSessionCRUD = Depends(UserSessionCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    api_token: Optional[HTTPAuthorizationCredentials] = Depends(api_token_security),
) -> User:

    user_auth: UserAuth = await get_current_user_auth(
        request=request,
        user_session_crud=user_session_crud,
        user_auth_crud=user_auth_crud,
        api_token=api_token,
    )
    if user_auth is None:
        raise not_authenticated_exception
    # `get` hides deactivated users. Sessions and api tokens of a deactivated user
    # must not authenticate.
    user = await user_crud.get(
        user_auth.user_id, raise_exception_if_none=not_authenticated_exception
    )
    if user_auth.is_managed_api_token:
        _raise_if_oidc_login_too_old_for_managed_api_token(user)
    return user


def _raise_if_oidc_login_too_old_for_managed_api_token(user: User):
    """Roles and study permissions of OIDC users are only synced at login, and MedLog does
    not learn when the provider drops a user. A managed token outlives the login, so it
    pauses once the last OIDC login is older than `API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS`.
    """
    max_age_days = config.API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS
    if max_age_days is None or user.last_oidc_login_at is None:
        return
    now = datetime.datetime.now(tz=datetime.UTC).replace(tzinfo=None)
    if user.last_oidc_login_at < now - datetime.timedelta(days=max_age_days):
        log.debug(
            f"Rejecting managed api token of user '{user.id}', last OIDC login is older than {max_age_days} days"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                f"API token paused: your last login via OpenID Connect is older than {max_age_days} days. "
                "Log in to MedLog in the browser once to reactivate your API tokens."
            ),
        )


async def get_current_user_by_session(
    request: Request,
    user_session_crud: UserSessionCRUD = Depends(UserSessionCRUD.get_crud),
    user_auth_crud: UserAuthCRUD = Depends(UserAuthCRUD.get_crud),
    user_crud: UserCRUD = Depends(UserCRUD.get_crud),
    api_token: Optional[HTTPAuthorizationCredentials] = Depends(api_token_security),
) -> User:
    """Like `get_current_user`, but refuses API tokens.

    For endpoints that must only be reachable from a browser session, e.g. the api token
    management. Otherwise a leaked token could mint new tokens that outlive its own expiry
    or revocation.
    """
    if api_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a browser session login. It can not be used with an API token.",
        )
    return await get_current_user(
        request=request,
        user_session_crud=user_session_crud,
        user_auth_crud=user_auth_crud,
        user_crud=user_crud,
        api_token=None,
    )


async def user_is_admin(
    user: Annotated[User, Security(get_current_user)],
) -> bool:
    if not config.ADMIN_ROLE_NAME in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not admin",
        )
    return True


async def user_is_usermanager(
    user: Annotated[User, Security(get_current_user)],
) -> bool:
    log.info(f"user: {user}")
    if not (
        config.USERMANAGER_ROLE_NAME in user.roles
        or config.ADMIN_ROLE_NAME in user.roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User is not user manager",
        )
    return True
