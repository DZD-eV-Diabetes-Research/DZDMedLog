from typing import Literal
from pydantic import BaseModel


class AuthScheme(BaseModel):
    name: str
    slug: str
    type: Literal["oidc", "credentials"]
    login_endpoint: str
    token_endpoint: str
