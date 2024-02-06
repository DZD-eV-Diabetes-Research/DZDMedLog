from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AnyUrl, SecretStr, AnyHttpUrl, validator, StringConstraints
from typing import List, Annotated, Optional, Literal, Dict
from pathlib import Path, PurePath
import socket
from textwrap import dedent


env_file_path = Path(__file__).parent / ".env"
# print(env_file)


class Config(BaseSettings):
    APP_NAME: str = "DZD MedLog"
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="WARNING"
    )
    # Webserver
    SERVER_UVICORN_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="The log level of the uvicorn server. If not defined it will be the same as LOG_LEVEL.",
    )

    SERVER_LISTENING_PORT: int = Field(default=8008)
    SERVER_LISTENING_HOST: str = Field(
        default="localhost",
        examples=["0.0.0.0", "localhost", "127.0.0.1", "176.16.8.123"],
    )
    # ToDo: Read https://fastapi.tiangolo.com/advanced/behind-a-proxy/ if that is of any help for better hostname/FQDN detection
    SERVER_HOSTNAME: Optional[str] = Field(
        default_factory=socket.gethostname,
        description="The (external) hostname/domainname where the API is available. Usally a FQDN in productive systems. If not defined, it will be automatically detected based on the hostname.",
        examples=["mydomain.com", "localhost:8008"],
    )
    SERVER_PROTOCOL: Optional[Literal["http", "https"]] = Field(
        default="http",
        description="The protocol detection can fail in certain reverse proxy situations. This option allows you to manually override the automatic detection",
    )

    SERVER_SESSION_SECRET: str = Field(
        description="The secret used to encrypt session state. Provide a long random string.",
        min_length=64,
    )

    def get_server_url(self) -> AnyHttpUrl:
        if self.SERVER_PROTOCOL is not None:
            proto = self.SERVER_PROTOCOL
        elif self.SERVER_LISTENING_HOST == 443:
            proto = "https"
        else:
            proto = "http"
        return AnyHttpUrl(f"{proto}://{self.SERVER_HOSTNAME}")

    SQL_DATABASE_URL: AnyUrl = Field(default="sqlite+aiosqlite:///./local.sqlite")

    ADMIN_USER_NAME: str = Field(default="admin")
    ADMIN_USER_PW: str = Field()
    ADMIN_USER_EMAIL: Optional[str] = Field(default=None)
    ADMIN_ROLE_NAME: str = Field(default="medlog-admin")
    USERMANAGER_ROLE_NAME: str = Field(default="medlog-user-manager")

    APP_CONFIG_PRESCRIBED_BY_DOC_ANSWERS: Dict = Field(
        default={
            "PRESCRIBED": "prescribed",
            "RECOMMENDED": "recommended",
            "NO": "no",
            "UNKNOWN": "unknown",
        }
    )

    AUTH_LOCAL_LOGIN_IS_ENABLED: bool = Field(
        default=True,
        description="Local DB users are enabled to login. You could disable this, when having an external OIDC provider.",
    )
    AUTH_LOCAL_USER_DB_REGISTER_ENABLED: Literal[False] = Field(
        default=False, description="Self registration of users is not supported yet."
    )

    AUTH_JWT_SECRET: str = Field(
        description="The secret used to sign the JWT tokens. Provide a long random string.",
        min_length=64,
    )
    AUTH_JWT_ALGORITHM: Literal["HS256"] = Field(
        default="HS256",
        description="The algorithm used to sign the JWT tokens. Only HS256 is supported atm",
    )
    AUTH_ACCESS_TOKEN_EXPIRES_MINUTES: int = Field(
        default=2,
        description=dedent(
            """These JWT access tokens serve two purposes: As a authorization key to access the API but also to store/cache userdata.
            The lifespan of the client's JWT access tokens is defined in minutes and is intentionally kept short. 
            These access tokens serve as a means to efficiently store encrypted user data, mitigating excessive database access. 
            However, it's essential to note that these tokens also encompass critical user information, including the user's deactivated status and roles.
            Any alterations to the deactivated status or user roles will only take effect after the access token undergoes a refresh. 
            Therefore, the design encourages regular token refreshes to ensure that the latest user status and role changes are reflected, 
            maintaining an optimal balance between security and responsiveness in accessing user-related information.
            """
        ),
    )
    AUTH_REFRESH_TOKEN_EXPIRES_MINUTES: int = Field(
        default=10080,
        description=dedent(
            """sets the duration, in minutes, for how long refresh tokens stay valid in the REST API. 
            Refresh tokens extend the lifespan of access tokens without making users log in again. 
            By adjusting this setting, you can balance security and user convenience, 
            deciding how long refresh tokens should remain active based on your application's needs."""
        ),
    )
    AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS: bool = Field(
        description="If true, users from different providers with the same name are merged into one user. If false users with same name will cause an error.",
        default=True,
    )
    AUTH_CHECK_REFRESH_TOKENS_FOR_REVOKATION: bool = Field(
        description=dedent(
            """If true, the tokens are checked against the database with every request if they are revoked.
                If false, the tokens will just expire according to `AUTH_ACCESS_TOKEN_EXPIRES_MINUTES`.
                Set this to True if you need a very strict access policy, where deactivated users get locked out immediately. 
                If you want to lower database traffic and quicker requests set this to False."""
        ),
        default=False,
    )

    class OpenIDConnectProvider(BaseSettings):
        PROVIDER_SLUG_NAME: Annotated[
            str,
            StringConstraints(
                strip_whitespace=True, to_lower=True, pattern=r"^[a-zA-Z0-9-]+$"
            ),
        ] = Field(
            description="The name of the OpenID Connect used in urls. Must be a unique name in all AUTH_OIDC_PROVIDERS.",
            default="openid-connect",
            max_length=64,
            min_length=3,
        )

        PROVIDER_DISPLAY_NAME: str = Field(
            description="The name of the OpenID Connect provider shown to the user.",
            default="My OpenID Connect Login",
        )
        CLIENT_ID: str = Field(
            description="The client id of the OpenID Connect provider."
        )
        CLIENT_SECRET: SecretStr = Field(
            description="The client secret of the OpenID Connect provider."
        )
        DISCOVERY_ENDPOINT: AnyUrl = Field(
            description="The discovery endpoint of the OpenID Connect provider."
        )
        SCOPES: List[str] = Field(
            description="", default=["openid", "profile", "email"]
        )
        USER_ID_ATTRIBUTE: str = Field(
            description="The attribute of the OpenID Connect provider that contains a unique id of the user.",
            default="preferred_username",
        )
        USER_DISPLAY_NAME_ATTRIBUTE: str = Field(
            description="The attribute of the OpenID Connect provider that contains the display name of the user.",
            default="display_name",
        )
        USER_MAIL_ATTRIBUTE: str = Field(
            description="The attribute of the OpenID Connect provider that contains a unique id of the user.",
            default="email",
        )
        USER_MAIL_VERIFIED_ATTRIBUTE: str = Field(
            description="The attribute of the OpenID Connect provider that contains the info if the email adress is verified.",
            default="email_verified",
        )
        USER_GROUP_ATTRIBUTE: str = Field(description="", default="groups")

        AUTO_CREATE_AUTHORIZED_USER: bool = Field(
            default=True,
            description="If a user does not exists in the local database, create the user on first authorization via the OIDC Provider.",
        )
        PREFIX_USER_ID_WITH_PROVIDER_NAME: bool = Field(
            description="To prevent naming collisions, the user id is prefixed with the provider name. HINT: 'AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS' will not work with 'PREFIX_USER_ID_WITH_PROVIDER_NAME' set to True.",
            default=False,
        )

    AUTH_OIDC_PROVIDERS: Optional[List[OpenIDConnectProvider]] = Field(
        description="Configure OpenID Connect (OIDC) provider settings for integrating with one or multiple external OIDC providers as the user backend.",
        default_factory=list,
    )

    @validator("AUTH_OIDC_PROVIDERS")
    def unique_provider_names(cls, AUTH_OIDC_PROVIDERS: List[OpenIDConnectProvider]):
        names = [prov.PROVIDER_SLUG_NAME for prov in AUTH_OIDC_PROVIDERS]
        if len(set(names)) < len(AUTH_OIDC_PROVIDERS):
            raise ValueError(
                "AUTH_OIDC_PROVIDERS config error. `PROVIDER_SLUG_NAME` must be unique accross all OIDC-provider entries."
            )
        return AUTH_OIDC_PROVIDERS

    ###### CONFIG END ######
    # mode_config is fixed variable  in pydantic-settings to control the behaviour of our settings model
    # https://docs.pydantic.dev/latest/api/base_model/#pydantic.main.BaseModel.model_config
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=env_file_path,
        env_file_encoding="utf-8",
    )
