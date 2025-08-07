from typing import (
    AsyncGenerator,
    List,
    Optional,
    Literal,
    Sequence,
    Annotated,
    Self,
    Dict,
)

from pydantic import BaseModel, Field


from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model.user_auth import AllowedAuthSchemeType

log = get_logger()
config = Config()


class AuthSchemeInfo(BaseModel):
    display_name: str
    auth_type: AllowedAuthSchemeType
    login_endpoint: str
    registration_endpoint: Optional[str] = None
    provider_slug: Optional[str] = None
