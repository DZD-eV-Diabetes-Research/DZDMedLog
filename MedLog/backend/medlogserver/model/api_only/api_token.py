from typing import Optional, Literal, Self
import datetime
import uuid

from pydantic import Field, computed_field

from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import MedLogBaseApiModel
from medlogserver.model.user_auth import UserAuth, API_TOKEN_NAME_MAX_LENGTH

# Upper bound for a chosen lifetime, also when the server allows tokens without expiry.
# Larger values overflow the expiry date calculation.
API_TOKEN_EXPIRY_DAYS_LIMIT = 3650

log = get_logger()
config = Config()


class ApiTokenManagementConfig(MedLogBaseApiModel):
    """Everything the web client needs to render the api token management UI."""

    enabled: bool = Field(
        description="Is the api token management available. If `false` the client should hide the token management UI, all `/api/user/me/api-token` endpoints answer with 403 and tokens created while it was enabled do not authenticate."
    )
    default_expiry_days: Optional[int] = Field(
        description="The lifetime a new token gets if `expires_in_days` is omitted on creation. `null` means such tokens never expire."
    )
    max_expiry_days: Optional[int] = Field(
        description="The longest lifetime a user may choose for a new token. `null` means there is no limit and `expires_in_days` may be `null` to create a token that never expires."
    )
    max_tokens_per_user: Optional[int] = Field(
        description="How many unexpired tokens a user may have at the same time. `null` means no limit."
    )
    oidc_login_max_age_days: Optional[int] = Field(
        description="Tokens of a user who logs in via OpenID Connect pause when the last OIDC login is older than this many days, and work again after the next login. `null` means they do not pause."
    )
    name_max_length: int = Field(
        default=API_TOKEN_NAME_MAX_LENGTH,
        description="Maximum length of a token name.",
    )
    requires_session_login: bool = Field(
        default=True,
        description="The token management endpoints can only be used with a browser session, never with an API token.",
    )


class ApiTokenCreate(MedLogBaseApiModel):
    name: str = Field(
        min_length=1,
        max_length=API_TOKEN_NAME_MAX_LENGTH,
        description="A name that helps to recognise the token later, e.g. the script or machine that uses it.",
        examples=["Nightly export script"],
    )
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=API_TOKEN_EXPIRY_DAYS_LIMIT,
        description=(
            "Lifetime of the token in days. Omit it to get `default_expiry_days` from `/api/config/api-token`. "
            "Must not exceed `max_expiry_days`. An explicit `null` creates a token that never expires, "
            "which is only allowed if `max_expiry_days` is `null`."
        ),
        examples=[30],
    )


class ApiTokenRead(MedLogBaseApiModel):
    id: uuid.UUID = Field(
        description="Identifies the token in the token management endpoints, e.g. to revoke it."
    )
    name: Optional[str] = Field(
        description="The name given on creation. `null` for tokens created via a token login endpoint."
    )
    token_prefix: str = Field(
        description="The public first part of the token (everything before the dot). Lets users match a token they have in use to this entry. The secret part can not be recalled."
    )
    created_via: Literal["token_management", "login"] = Field(
        description="`token_management`: created by the user in the token management. `login`: issued by a token login endpoint (`/api/auth/basic/login/token` or the OIDC token login); such a token is bound to that login and stops working with it."
    )
    created_at: datetime.datetime = Field(description="Creation time (UTC).")
    expires_at: Optional[datetime.datetime] = Field(
        description="Expiry time (UTC). `null` if the token never expires on its own."
    )
    last_used_at: Optional[datetime.datetime] = Field(
        description="Last time (UTC) the token was used, accurate to about a minute. `null` if it was never used."
    )

    @computed_field(
        description="`true` if the token reached its expiry time. Expired tokens are removed by a background job after a while."
    )
    @property
    def expired(self) -> bool:
        if self.expires_at is None:
            return False
        return self.expires_at <= datetime.datetime.now(tz=datetime.UTC).replace(
            tzinfo=None
        )

    @classmethod
    def from_user_auth(cls, user_auth: UserAuth) -> Self:
        expires_at = None
        if user_auth.expires_at_epoch_time is not None:
            expires_at = datetime.datetime.fromtimestamp(
                user_auth.expires_at_epoch_time, tz=datetime.UTC
            ).replace(tzinfo=None)
        return cls(
            id=user_auth.id,
            name=user_auth.api_token_name,
            token_prefix=user_auth.api_token_id,
            created_via=(
                "token_management" if user_auth.is_managed_api_token else "login"
            ),
            created_at=user_auth.created_at,
            expires_at=expires_at,
            last_used_at=user_auth.api_token_last_used_at,
        )


class ApiTokenCreated(ApiTokenRead):
    token: str = Field(
        description="The complete token to send as `Authorization: Bearer <token>`. It is only shown in this response and can not be recalled later."
    )
