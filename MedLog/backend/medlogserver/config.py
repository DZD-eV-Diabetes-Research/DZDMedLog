from typing import List, Annotated, Optional, Literal, Dict
from typing_extensions import Self
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pydantic import (
    Field,
    SecretStr,
    AnyHttpUrl,
    field_validator,
    StringConstraints,
    model_validator,
)

from pathlib import Path, PurePath
import socket
from textwrap import dedent
from medlogserver.utils import get_random_string, val_means_true, slugify_string

env_file_path = os.environ.get("MEDLOG_DOT_ENV_FILE", Path(__file__).parent / ".env")


class Config(BaseSettings):
    APP_NAME: str = "DZDMedLog"
    DOCKER_MODE: bool = False
    FRONTEND_FILES_DIR: str = Field(
        description="The generated nuxt dir that contains index.html,...",
        default=str(
            Path(Path(__file__).parent.parent.parent, "frontend/.output/public")
        ),
    )
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="INFO"
    )
    DEMO_MODE: bool = Field(
        default=False,
        description="If set to yes, the database will initiate with some demo data and most config mandatory config vars, like crypto secrets will be set to something random.",
    )

    @model_validator(mode="before")
    def demo_mode(self_data: dict):
        if val_means_true(self_data.get("DEMO_MODE", False)):
            if not self_data.get("SERVER_SESSION_SECRET", None):
                self_data["SERVER_SESSION_SECRET"] = get_random_string(64)
            if not self_data.get("ADMIN_USER_PW", None):
                self_data["ADMIN_USER_PW"] = "adminadmin"
            if not self_data.get("APP_PROVISIONING_DATA_YAML_FILES", None):
                if bool(self_data["DOCKER_MODE"]):
                    self_data["APP_PROVISIONING_DATA_YAML_FILES"] = [
                        str(
                            Path(
                                os.getenv("MEDLOG_DOCKER_BASEDIR", "/opt/medlog"),
                                "provisioning/database/demo_data/single_study_demo_data.yaml",
                            )
                        )
                    ]
                else:
                    self_data["APP_PROVISIONING_DATA_YAML_FILES"] = [
                        str(
                            Path(
                                Path(__file__).parent.parent,
                                "provisioning_data/demo_data/single_study_demo_data.yaml",
                            )
                        )
                    ]
        return self_data

    DEBUG_SQL: bool = Field(
        default=False,
        description="If set to true, the sql engine will print out all sql queries to the log.",
    )
    # Webserver
    SERVER_UVICORN_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description="The log level of the uvicorn server. If not defined it will be the same as LOG_LEVEL.",
    )

    SERVER_LISTENING_PORT: int = Field(default=8888)
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

    SERVER_SESSION_SECRET: SecretStr = Field(
        description="The secret used to encrypt session state. Provide a long random string.",
        min_length=64,
    )

    SET_SESSION_COOKIE_SECURE: bool = Field(
        default=True,
        description="if you want to run the app on a non ssl connection set this to false. e.g for local development.",
    )

    def get_server_url(self) -> str:
        if self.SERVER_PROTOCOL is not None:
            proto = self.SERVER_PROTOCOL
        elif self.SERVER_LISTENING_PORT == 443:
            proto = "https"

        port = ""
        if self.SERVER_LISTENING_PORT not in [80, 443]:
            port = f":{self.SERVER_LISTENING_PORT}"
        return f"{proto}://{self.SERVER_HOSTNAME}{port}"

    CLIENT_URL: Optional[str] = Field(
        default=None,
        description="The URL where the client is hosted. Usualy it comes with the server",
    )

    @model_validator(mode="after")
    def set_empty_client_url(self: Self):
        if self.CLIENT_URL is None:
            self.CLIENT_URL = str(self.get_server_url())
        return self

    SQL_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./local.sqlite",
        description="Connection URL for the database based on the RFC-1738 standard. Mind the 3 (instead of 2) leading slashes in sqlite file pathes https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#connect-strings",
    )

    ADMIN_USER_NAME: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=128,
            min_length=3,
        ),
    ] = Field(default="admin")
    ADMIN_USER_PW: SecretStr = Field()
    ADMIN_USER_EMAIL: Optional[str] = Field(default=None)
    ADMIN_ROLE_NAME: str = Field(default="medlog-admin")
    USERMANAGER_ROLE_NAME: str = Field(default="medlog-user-manager")
    BACKGROUND_WORKER_START_IN_EXTRA_PROCESS: bool = Field(
        default=True,
        description="If set to True the background service will start in an extra Process next to the webserver. If set to False, the backgroundworker will not run. You have to setup an extra instance of the worker.",
    )
    BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN: Optional[int] = Field(
        description="Jobs like the import of new Arzneimitteldata, are queued in the database. For debuging porposes you might want to keep the job info in the queue table for a while. If set to 'None', finished jobs will remain in the DB forever.",
        default=60 * 24 * 1,
        # default=1,
    )
    APP_PROVISIONING_DATA_YAML_FILES: Optional[List[str]] = Field(
        default_factory=list,
        description="A list if yaml files to serialize and load into MedLog models and into the DB ",
    )

    APP_PROVISIONING_DEFAULT_DATA_YAML_FILE: str = Field(
        description="Default data like some background jobs and vocabulary that is always loaded in the database. Under normal circustances this is nothing you need to changed. if you need to provision data like a Study into the database use the APP_PROVISIONING_DATA_YAML_FILES param.",
        default=str(Path(Path(__file__).parent, "default_data.yaml")),
    )

    APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT: bool = Field(
        default=False,
        description="If set to True; all user can access all new created studies, edit settings and create and edit interviews. This may be utile on small instances with a trusted userbase where user management is not wanted/needed.",
    )

    AUTH_BASIC_LOGIN_IS_ENABLED: bool = Field(
        default=True,
        description="Local DB users are enabled to login. You could disable this, when having an external OIDC provider.",
    )
    AUTH_BASIC_USER_DB_REGISTER_ENABLED: Literal[False] = Field(
        default=False, description="Self registration of users is not supported yet."
    )

    API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES: Optional[int] = Field(
        default=60 * 24 * 7,  # one week
        description="If an api access token was created (on login or in token management) they should expire after this time.",
    )

    AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS: bool = Field(
        description="OPTION NOT IMPLEMENTED YET! If true, users from different providers with the same name are merged into one user. If false users with same name will cause an error. ",
        default=True,
    )

    class OpenIDConnectProvider(BaseSettings):
        ENABLED: bool = Field(default=False, description="Is the provider enabled")
        PROVIDER_DISPLAY_NAME: str = Field(
            description="The unique name of the OpenID Connect provider shown to the user.",
            default="My OpenID Connect Login",
        )

        def get_provider_name_slug(self):
            return slugify_string(self.PROVIDER_DISPLAY_NAME)

        AUTO_LOGIN: Optional[bool] = Field(
            default=False,
            description="If set to true, the client will try to immediatly redirect to this provider instead of showing the login page.",
        )
        CONFIGURATION_ENDPOINT: str = Field(
            description="The discovery endpoint of the OpenID Connect provider."
        )
        CLIENT_ID: str = Field(
            description="The client id of the OpenID Connect provider."
        )
        CLIENT_SECRET: SecretStr = Field(
            description="The client secret of the OpenID Connect provider."
        )
        SCOPES: List[str] = Field(
            description="", default=["openid", "profile", "email"]
        )

        def get_scopes_as_string(self):
            return " ".join(self.SCOPES)

        USER_NAME_ATTRIBUTE: str = Field(
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
        USER_GROUPS_ATTRIBUTE: str = Field(description="", default="groups")

        AUTO_CREATE_AUTHORIZED_USER: bool = Field(
            default=True,
            description="If a user does not exists in the local database, create the user on first authorization via the OIDC Provider.",
        )
        PREFIX_USERNAME_WITH_PROVIDER_SLUG: bool = Field(
            default=False,
            description="To prevent username colliction between different OIDC providers, we can prefix the usernames from the OIDC provider with it slug.",
        )
        ROLE_MAPPING: Dict[str, List[str]] = Field(
            default_factory=dict,
            description="""A JSON to map OIDC groups to DZDMedLog Roles. e.g. `{"oidc_appadmins":["medlog-user-manager"],"admins":["medlog-admins"]}`""",
        )

    AUTH_OIDC_TOKEN_STORAGE_SECRET: Optional[str] = Field(
        description="Random string to encrypt the oidc access and refresh token for storing it in the database.",
        default="placeholder_until_todo_see_below",
    )  # todo only needed if AUTH_OIDC_PROVIDERS is not empty. Create a model_validation
    AUTH_OIDC_PROVIDERS: Optional[List[OpenIDConnectProvider]] = Field(
        description="Configure additional/alternative OpenID Connect (OIDC) provider settings for integrating.",
        default_factory=list,
    )

    @field_validator("AUTH_OIDC_PROVIDERS")
    def unique_provider_names(cls, AUTH_OIDC_PROVIDERS: List[OpenIDConnectProvider]):
        names = [prov.get_provider_name_slug() for prov in AUTH_OIDC_PROVIDERS]
        if len(set(names)) < len(AUTH_OIDC_PROVIDERS):
            raise ValueError(
                f"AUTH_OIDC_PROVIDERS config error. `PROVIDER_DISPLAY_NAME` must result in unique slugs accross all OIDC-provider entries. OIDC Provider Slugs:  {names}"
            )
        return AUTH_OIDC_PROVIDERS

    AI_DATA_IMPORTER_FLUSH_AFTER_N_ROWS: int = Field(
        default=1000,
        description="When reading the Arzneimittelindex data files, write every n rows to the database. Lower this number in a low memory env.",
    )

    # Availabe modules live in MedLog/backend/medlogserver/model/drug_data/importers/__init__.py
    DRUG_IMPORTER_PLUGIN: Literal[
        "WidoGkvArzneimittelindex52", "MmmiPharmaindex1_32", "DummyDrugImporterV1"
    ] = Field(
        default="DummyDrugImporterV1",
        description="Depending on the drug database that is used, we can define an importer.",
    )

    DRUG_IMPORTER_BATCH_SIZE: int = Field(
        default=200000,
        description="If the drug import supports batching, this is the size per batch. The trade of are some speed bumps, while drug importing, versus memory consumption. On a low memory machine decrease this value.",
    )

    DRUG_SEARCHENGINE_CLASS: Literal["GenericSQLDrugSearch"] = Field(
        description="The search engine used in the background to answer drug search requests.",
        default="GenericSQLDrugSearch",
    )
    DRUG_TABLE_PROVISIONING_SOURCE_DIR: str = Field(
        description="If MedLog is booted with an empty drug database, it will check if a source data set of the GKV Arzneimittel Index is located in this dir",
        default=str(
            Path(
                Path(__file__).parent.parent, "provisioning_data/dummy_drugset/20241126"
            ).absolute()
        ),
    )

    DRUG_DATA_IMPORT_MAX_ROWS: Optional[int] = Field(
        description="For debuging or demo purposes you can limit the amount of drug entries that are parsed and import while the drug importer runs. This speeds up the import process massivly but you will not have all drug entries.",
        default=None,
    )

    EXPORT_CACHE_DIR: str = Field(
        default="./export_cache",
        description="The directory to store the result of export jobs (CSV files, JSON files,...).",
    )

    ###### CONFIG END ######
    # "class Config:" is a pydantic-settings pre-defined config class to control the behaviour of our settings model
    # you could call it a "meta config" class
    # if you dont know what this is you can ignore it.
    # https://docs.pydantic.dev/latest/api/base_model/#pydantic.main.BaseModel.model_config

    class Config:
        env_nested_delimiter = "__"
        env_file = env_file_path
        env_file_encoding = "utf-8"
        extra = "ignore"
