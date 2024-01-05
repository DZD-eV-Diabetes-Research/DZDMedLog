from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl
from typing import List, Annotated
from pathlib import Path, PurePath

env_file_path = Path(__file__).parent / ".env"
# print(env_file)


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=env_file_path,
        env_file_encoding="utf-8",
    )

    sqldatabase_url: AnyUrl = Field(default="sqlite+aiosqlite:///./local.db")

    class OpenIDConnect(BaseSettings):
        client_id: str = Field(
            description="The client id of the OpenID Connect provider."
        )
        client_secret: str = Field(
            description="The client secret of the OpenID Connect provider."
        )
        discovery_endpoint: AnyUrl = Field(
            description="The discovery endpoint of the OpenID Connect provider."
        )
        scopes: List[str] = Field(
            description="", default=["openid", "profile", "email"]
        )
        user_id_attribute: str = Field(
            description="The attribute of the OpenID Connect provider that contains a unique id of the user.",
            default="preferred_username",
        )
        user_display_name_attribute: str = Field(
            description="The attribute of the OpenID Connect provider that contains the display name of the user.",
            default="display_name",
        )
        user_mail_attribute: str = Field(
            description="The attribute of the OpenID Connect provider that contains a unique id of the user.",
            default="email",
        )
        jwt_secret: str = Field(description="The secret used to sign the JWT tokens.")

    oidc: OpenIDConnect = Field(description="OpenID Connect settings.")
