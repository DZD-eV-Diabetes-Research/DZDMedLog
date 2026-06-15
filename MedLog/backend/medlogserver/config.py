from typing import List, Annotated, Optional, Literal, Dict
from typing_extensions import Self
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pydantic import (
    Field,
    SecretStr,
    field_validator,
    StringConstraints,
    model_validator,
)
import inspect
from pathlib import Path, PurePath
import socket
from textwrap import dedent
from medlogserver.utils import (
    get_random_string,
    val_means_true,
    slugify_string,
    normalize_sqlite_url,
)

env_file_path = os.environ.get("MEDLOG_DOT_ENV_FILE", Path(__file__).parent / ".env")


class Config(BaseSettings):
    APP_NAME: str = Field(
        default="DZDMedLog",
        description=(
            "Display name of the application. Used in log output, session cookie names, "
            "and health-check responses."
        ),
        examples=["DZDMedLog", "MyMedLog"],
    )
    DOCKER_MODE: bool = Field(
        default=False,
        description=(
            "Set to True when running inside Docker. "
            "Adjusts internal path resolution for provisioning files to use the Docker base directory "
            "defined by the MEDLOG_DOCKER_BASEDIR environment variable (default: /opt/medlog). "
            "The official Dockerfile sets this automatically via ENV DOCKER_MODE=1."
        ),
    )
    FRONTEND_FILES_DIR: str = Field(
        description=(
            "Path to the built Nuxt frontend output directory that contains index.html and all static assets. "
            "This directory is served by the backend as the web client. "
            "In development, run `npm run build` inside the frontend directory to generate it."
        ),
        default=str(
            Path(Path(__file__).parent.parent.parent, "frontend/.output/public")
        ),
        examples=["/opt/medlog/frontend/.output/public", "./frontend/.output/public"],
    )
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = Field(
        default="INFO",
        description="Verbosity of the application logger. DEBUG produces the most output; CRITICAL the least.",
    )
    LOG_DISABLE_COLORS: bool = Field(
        description=(
            "If True, log output will have no ANSI color coding. "
            "Useful for log aggregators or terminals that do not support color escape codes."
        ),
        default=False,
    )
    DEMO_MODE: bool = Field(
        default=False,
        description=(
            "If True, the application starts in demonstration mode: "
            "the database is seeded with sample data, and mandatory secrets such as "
            "SERVER_SESSION_SECRET are auto-generated if not provided. "
            "Do not use in production."
        ),
    )

    @model_validator(mode="before")
    def demo_mode(self_data: dict):
        if val_means_true(self_data.get("DEMO_MODE", False)):
            if not self_data.get("SERVER_SESSION_SECRET", None):
                self_data["SERVER_SESSION_SECRET"] = get_random_string(64)
            if not self_data.get("ADMIN_USER_PW", None):
                self_data["ADMIN_USER_PW"] = "adminadmin"
            if not self_data.get("APP_PROVISIONING_DATA_YAML_FILES", None):
                if "DOCKER_MODE" in self_data and bool(self_data["DOCKER_MODE"]):
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
        description=(
            "If True, the SQLAlchemy engine echoes all generated SQL statements to the log. "
            "Useful for debugging database queries."
        ),
    )
    # Webserver
    SERVER_UVICORN_LOG_LEVEL: Optional[str] = Field(
        default=None,
        description=(
            "Log level for the Uvicorn ASGI server. Accepts the same values as LOG_LEVEL. "
            "If not set, falls back to the value of LOG_LEVEL."
        ),
    )

    SERVER_LISTENING_PORT: int = Field(
        default=8888,
        description="TCP port the Uvicorn server binds to and listens on.",
        examples=[8888, 8080, 80, 443],
    )
    SERVER_LISTENING_HOST: str = Field(
        default="localhost",
        description=(
            "Network interface the Uvicorn server binds to. "
            "Use '0.0.0.0' to accept connections on all interfaces (required in Docker). "
            "Use 'localhost' or '127.0.0.1' to restrict to the local machine only."
        ),
        examples=["0.0.0.0", "localhost", "127.0.0.1", "176.16.8.123"],
    )
    # ToDo: Read https://fastapi.tiangolo.com/advanced/behind-a-proxy/ if that is of any help for better hostname/FQDN detection
    SERVER_HOSTNAME: Optional[str] = Field(
        default_factory=socket.gethostname,
        description=(
            "External hostname or domain name under which the API is publicly reachable. "
            "Usually a fully-qualified domain name (FQDN) in production. "
            "If not set, the system hostname is used as a fallback. "
            "This value is used to build the server URL and OAuth redirect URIs."
        ),
        examples=["medlog.example.com", "localhost", "10.0.0.5"],
    )
    SERVER_PROTOCOL: Optional[Literal["http", "https"]] = Field(
        default="http",
        description=(
            "Protocol used to reach the server from the outside. "
            "Automatic detection can fail behind reverse proxies that terminate TLS — "
            "set this explicitly to 'https' when serving over SSL."
        ),
        examples=["http", "https"],
    )

    SERVER_SESSION_SECRET: SecretStr = Field(
        description=(
            "Secret key used to sign and encrypt browser session cookies. "
            "Must be at least 64 characters long. "
            "Use a cryptographically random string and keep it private — "
            "rotating this value invalidates all active sessions."
        ),
        min_length=64,
    )

    SET_SESSION_COOKIE_SECURE: bool = Field(
        default=True,
        description=(
            "If True, session cookies are only sent over HTTPS (the Secure flag is set). "
            "Set to False for local development over plain HTTP, but never in production."
        ),
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
        description=(
            "URL where the web client is hosted. "
            "Usually the client is bundled with the server and this can be left unset — "
            "it is then derived automatically from SERVER_PROTOCOL, SERVER_HOSTNAME, and SERVER_LISTENING_PORT."
        ),
        examples=["https://medlog.example.com", "http://localhost:8888"],
    )
    BRANDING_SUPPORT_EMAIL_ADDRESS: Optional[str] = Field(
        default=None,
        description=(
            "Support email address displayed in the web client's help text. "
            "Leave unset to hide the support contact from the UI."
        ),
        examples=["support@example.com"],
    )

    @model_validator(mode="after")
    def set_empty_client_url(self: Self):
        if self.CLIENT_URL is None:
            self.CLIENT_URL = str(self.get_server_url())
        return self

    SQL_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./../../../medlog.sqlite",
        examples=[
            "sqlite+aiosqlite:///local.db",  # relative SQLite path -> resolved to absolute
            "sqlite+aiosqlite:////opt/data.db",  # absolute POSIX SQLite path -> preserved
            "sqlite+aiosqlite:///:memory:",  # in-memory SQLite
            "sqlite+aiosqlite:///./local2.sqlite",  # relative async SQLite path
            "postgresql+psycopg://user:pass@localhost:5432/mydb",  # PostgreSQL
        ],
        description=inspect.cleandoc(
            """
        The database URL for the application. Only SQLite (via `sqlite+aiosqlite`)
        and PostgreSQL (via `postgresql+psycopg`) URLs are supported.

        `sqlite+aiosqlite` and `postgresql+psycopg` specify the async DB drivers used
        by SQLAlchemy's async engine. They are required so the application can run
        database operations asynchronously.

        SQLite URL rules (per SQLAlchemy):
        - Relative paths: sqlite+aiosqlite:///relative/path.db  (three slashes '///')
            Example: sqlite+aiosqlite:///local.db -> resolved relative to the main script directory.
        - Absolute POSIX paths: sqlite+aiosqlite:////absolute/path.db  (four slashes '////')
            Example: sqlite+aiosqlite:////opt/data.db -> absolute path preserved.
        - Windows absolute paths: sqlite+aiosqlite:///C:/absolute/path.db
            (drive letters detected automatically).
        - Memory databases: sqlite+aiosqlite:///:memory: remain unchanged.

        Application behavior:
        All SQLite relative paths are automatically resolved to absolute paths
        relative to the main script directory, in contrast to the default SQLAlchemy behavior.

        PostgreSQL URLs follow the standard async SQLAlchemy format:
        postgresql+psycopg://user:password@host:port/dbname

        Other database engines or drivers are not supported.
    """
        ),
    )

    @model_validator(mode="after")
    def normalize_sqllite_db_url(self):
        self.SQL_DATABASE_URL = normalize_sqlite_url(self.SQL_DATABASE_URL)
        return self

    ADMIN_USER_NAME: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=128,
            min_length=3,
        ),
    ] = Field(
        default="admin",
        description=(
            "Username for the built-in administrator account created on first startup. "
            "Must be between 3 and 128 characters. "
            "This account always has full admin privileges regardless of role mappings."
        ),
        examples=["admin", "medlog-admin"],
    )
    ADMIN_USER_PW: SecretStr = Field(
        description=(
            "Password for the built-in administrator account. "
            "Required unless DEMO_MODE is True (which sets it to 'adminadmin'). "
            "Choose a strong password for any non-demo deployment."
        ),
    )
    ADMIN_USER_EMAIL: Optional[str] = Field(
        default=None,
        description="Email address for the built-in administrator account. Optional.",
        examples=["admin@example.com"],
    )
    ADMIN_ROLE_NAME: str = Field(
        default="medlog-admin",
        description=(
            "Name of the application-level administrator role. "
            "Users with this role have full access to all studies, user management, and system settings. "
            "Change this if your organisation uses a different naming convention, "
            "and update any OIDC ROLE_MAPPING accordingly."
        ),
        examples=["medlog-admin", "app-admin"],
    )
    USERMANAGER_ROLE_NAME: str = Field(
        default="medlog-user-manager",
        description=(
            "Name of the user-manager role. "
            "Users with this role can create, edit, and deactivate user accounts "
            "but cannot change system settings. "
            "Change this if your organisation uses a different naming convention, "
            "and update any OIDC ROLE_MAPPING accordingly."
        ),
        examples=["medlog-user-manager", "user-admin"],
    )
    BACKGROUND_WORKER_START_IN_EXTRA_PROCESS: bool = Field(
        default=True,
        description=(
            "If True, the background worker (responsible for drug data imports, provisioning, etc.) "
            "is launched automatically alongside the web server in a separate OS process. "
            "If False, the worker is not started — you must run a second instance manually "
            "using the dedicated worker entry point."
        ),
    )
    BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN: Optional[int] = Field(
        description=(
            "How many minutes to keep completed background job records in the database before deleting them. "
            "Keeping records for a while is useful for debugging. "
            "Set to None to retain finished job records indefinitely."
        ),
        default=60 * 24 * 1,
    )
    APP_PROVISIONING_DATA_YAML_FILES: Optional[List[str]] = Field(
        default_factory=list,
        description=(
            "List of absolute paths to YAML files whose content is deserialized into MedLog models "
            "and loaded into the database on startup. "
            "Use this to pre-populate studies, users, or other entities in a fresh deployment. "
            "In DEMO_MODE a sample dataset is added automatically."
        ),
        examples=[
            ["/opt/medlog/provisioning/my_study.yaml"],
            ["./provisioning_data/demo_data/single_study_demo_data.yaml"],
        ],
    )

    APP_PROVISIONING_DEFAULT_DATA_YAML_FILE: str = Field(
        description=(
            "Path to the built-in default data YAML file that is always loaded into the database on startup. "
            "It contains baseline background jobs, vocabularies, and system defaults required for the app to function. "
            "Under normal circumstances you do not need to change this. "
            "To provision custom data such as studies, use APP_PROVISIONING_DATA_YAML_FILES instead."
        ),
        default=str(Path(Path(__file__).parent, "default_data.yaml")),
    )

    APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT: bool = Field(
        default=False,
        description=(
            "If True, all users can access all newly created studies and edit interviews "
            "without being explicitly granted permissions. "
            "Useful for small, trusted deployments where fine-grained access control is not needed. "
            "Has no effect on existing studies — only newly created studies inherit this default."
        ),
    )

    AUTH_BASIC_LOGIN_IS_ENABLED: bool = Field(
        default=True,
        description=(
            "Allow users with locally stored credentials (username + password) to log in. "
            "Disable when authentication is handled entirely by an external OIDC provider "
            "and you want to prevent direct password-based logins."
        ),
    )
    AUTH_BASIC_USER_DB_REGISTER_ENABLED: Literal[False] = Field(
        default=False,
        description=(
            "NOT YET IMPLEMENTED. Placeholder for a future self-registration feature. "
            "Self-registration of users is currently not supported; "
            "this field is locked to False and cannot be enabled."
        ),
    )

    API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES: Optional[int] = Field(
        default=60 * 24 * 7,  # one week
        description=(
            "How many minutes an API access token remains valid after it is issued. "
            "Applies to tokens created via login or the token management endpoint. "
            "Set to None for tokens that never expire (not recommended for production)."
        ),
        examples=[60, 1440, 10080],
    )

    AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS: bool = Field(
        default=True,
        description=(
            "NOT YET IMPLEMENTED. Placeholder for a future cross-provider user-merge feature. "
            "When implemented: if True, a user authenticating via a different provider but with the same "
            "username as an existing account will be merged into that account. "
            "If False, a duplicate username from a second provider will raise an error. "
            "Currently has no effect."
        ),
    )

    class OpenIDConnectProvider(BaseSettings):
        ENABLED: bool = Field(
            default=False,
            description="Set to True to activate this OIDC provider. If False, the provider is ignored at startup.",
        )
        PROVIDER_DISPLAY_NAME: str = Field(
            description=(
                "Display name shown on the login page for this provider. "
                "Must be unique across all configured OIDC providers."
            ),
            default="My OpenID Connect Login",
            examples=["Keycloak", "Azure AD", "Google"],
        )

        def get_provider_name_slug(self):
            return slugify_string(self.PROVIDER_DISPLAY_NAME)

        AUTO_LOGIN: Optional[bool] = Field(
            default=False,
            description=(
                "If True, the client immediately redirects to this provider's login page "
                "instead of showing MedLog's own login form. "
                "Only meaningful when exactly one OIDC provider is configured."
            ),
        )
        CONFIGURATION_ENDPOINT: str = Field(
            description=(
                "OpenID Connect discovery document URL of the provider (the 'well-known' endpoint). "
                "MedLog fetches the authorization, token, and JWKS endpoints from this URL automatically."
            ),
            examples=[
                "https://keycloak.example.com/realms/myrealm/.well-known/openid-configuration",
                "https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration",
            ],
        )
        CLIENT_ID: str = Field(
            description="Client ID registered for MedLog in the OIDC provider.",
            examples=["medlog-client", "abc123xyz"],
        )
        CLIENT_SECRET: SecretStr = Field(
            description="Client secret registered for MedLog in the OIDC provider. Keep this value private.",
        )
        SCOPES: List[str] = Field(
            default=["openid", "profile", "email", "offline_access"],
            description=(
                "OAuth2/OIDC scopes to request from the provider. "
                "The 'offline_access' scope requests a refresh token, which keeps the session alive "
                "without requiring the user to log in again after the access token expires. "
                "Remove it if your provider does not support refresh tokens."
            ),
            examples=[["openid", "profile", "email", "offline_access"]],
        )

        def get_scopes_as_string(self):
            return " ".join(self.SCOPES)

        USER_NAME_ATTRIBUTE: str = Field(
            description=(
                "Claim in the OIDC ID token that contains the unique, stable username used as "
                "the MedLog account identifier. This value must be unique per user and must not change over time."
            ),
            default="preferred_username",
            examples=["preferred_username", "sub", "upn"],
        )
        USER_DISPLAY_NAME_ATTRIBUTE: str = Field(
            description=(
                "Claim in the OIDC ID token used as the user's display name in the MedLog UI. "
                "Note: the default 'display_name' is not a standard OIDC claim — "
                "common alternatives are 'name' or 'given_name'."
            ),
            default="display_name",
            examples=["display_name", "name", "given_name"],
        )
        USER_MAIL_ATTRIBUTE: str = Field(
            description="Claim in the OIDC ID token that contains the user's email address.",
            default="email",
            examples=["email"],
        )
        USER_GROUPS_ATTRIBUTE: str = Field(
            description=(
                "Claim in the OIDC ID token that contains the list of groups the user belongs to. "
                "Used for ROLE_MAPPING and STUDY_PERMISSION_MAPPING. "
                "The attribute name varies by provider — common values are 'groups' or 'roles'."
            ),
            default="groups",
            examples=["groups", "roles", "cognito:groups"],
        )

        AUTO_CREATE_AUTHORIZED_USER: bool = Field(
            default=True,
            description=(
                "If True, a new MedLog user account is created automatically on the first login "
                "via this OIDC provider when no matching local account exists. "
                "If False, only users that already have a local account can log in via OIDC."
            ),
        )
        AUTO_CREATE_STUDY_FROM_MAPPING: bool = Field(
            default=False,
            description=(
                "If a study referenced in STUDY_PERMISSION_MAPPING does not exist in the "
                "database, create it automatically on the first OIDC login that triggers "
                "the mapping. Useful when studies are managed entirely via the OIDC "
                "configuration. Default is False: missing studies produce a warning and "
                "are skipped."
            ),
        )
        PREFIX_USERNAME_WITH_PROVIDER_SLUG: bool = Field(
            default=False,
            description=(
                "If True, the provider's URL-safe slug is prepended to usernames from this provider "
                "(e.g. 'keycloak__john.doe'). "
                "Prevents username collisions when multiple OIDC providers are configured "
                "and users from different providers could share the same username."
            ),
        )
        ROLE_MAPPING: Dict[str, List[str]] = Field(
            default_factory=dict,
            description=(
                "Maps OIDC group names to MedLog application roles. "
                "Each key is an OIDC group name; the value is a list of MedLog role names to assign. "
                "Available built-in roles are defined by ADMIN_ROLE_NAME and USERMANAGER_ROLE_NAME."
            ),
            examples=[
                {"oidc_appadmins": ["medlog-admin"], "oidc_usermgrs": ["medlog-user-manager"]}
            ],
        )
        STUDY_PERMISSION_MAPPING: Dict[str, Dict[str, List[str]]] = Field(
            default_factory=dict,
            description=(
                "Maps OIDC group membership to per-study permissions. "
                "Top-level key is the study name; each inner key is an OIDC group name; "
                "the value is a list of permissions to grant. "
                "Valid permissions: is_study_interviewer, is_study_viewer, is_study_admin."
            ),
            examples=[
                dedent("""{
                            "MyStudyName": {
                                "medlog-oidc-group-interviewer": [
                                "is_study_interviewer"
                                ],
                                "medlog-oidc-group-exporter": [
                                "is_study_viewer"
                                ],
                                "medlog-oidc-group-admin": [
                                "is_study_admin"
                                ],
                                "medlog-oidc-group-user-manager": [
                                "is_study_admin"
                                ]
                            }
                            }
                       """)
            ],
        )

    AUTH_OIDC_TOKEN_STORAGE_SECRET: Optional[str] = Field(
        description=(
            "Secret string used to encrypt OIDC access and refresh tokens before storing them in the database. "
            "Required when AUTH_OIDC_PROVIDERS is non-empty — provide a long random string and keep it stable across restarts. "
            "Rotating this value invalidates all stored OIDC tokens and forces all OIDC users to re-authenticate. "
            "If no OIDC providers are configured, this value is auto-generated (tokens are never stored in that case)."
        ),
        default=None,
    )
    AUTH_OIDC_PROVIDERS: Optional[List[OpenIDConnectProvider]] = Field(
        description=(
            "List of OpenID Connect (OIDC) provider configurations for federated authentication. "
            "Each entry represents one external identity provider (e.g. Keycloak, Azure AD). "
            "Leave empty to use only local username/password login."
        ),
        default_factory=list,
    )

    @model_validator(mode="after")
    def validate_oidc_token_storage_secret(self: Self):
        if self.AUTH_OIDC_TOKEN_STORAGE_SECRET is None:
            if self.AUTH_OIDC_PROVIDERS:
                raise ValueError(
                    "AUTH_OIDC_TOKEN_STORAGE_SECRET must be set when AUTH_OIDC_PROVIDERS is configured. "
                    "Provide a long random string (64+ characters)."
                )
            self.AUTH_OIDC_TOKEN_STORAGE_SECRET = get_random_string(64)
        return self

    @field_validator("AUTH_OIDC_PROVIDERS")
    def unique_provider_names(cls, AUTH_OIDC_PROVIDERS: List[OpenIDConnectProvider]):
        names = [prov.get_provider_name_slug() for prov in AUTH_OIDC_PROVIDERS]
        if len(set(names)) < len(AUTH_OIDC_PROVIDERS):
            raise ValueError(
                f"AUTH_OIDC_PROVIDERS config error. `PROVIDER_DISPLAY_NAME` must result in unique slugs accross all OIDC-provider entries. OIDC Provider Slugs:  {names}"
            )
        return AUTH_OIDC_PROVIDERS

    # Available modules live in MedLog/backend/medlogserver/model/drug_data/importers/__init__.py
    DRUG_IMPORTER_PLUGIN: Literal["MMIPharmindex1_32", "DummyDrugImporterV1"] = Field(
        default="DummyDrugImporterV1",
        description=(
            "Selects the drug data importer plugin. "
            "'DummyDrugImporterV1' uses a small built-in sample dataset, suitable for development and demos. "
            "'MMIPharmindex1_32' imports from the MMI Pharmindex format (version 1.32), "
            "used with German GKV Arzneimittelverzeichnis data."
        ),
        examples=["DummyDrugImporterV1", "MMIPharmindex1_32"],
    )
    DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB: bool = Field(
        default=False,
        description=(
            "If True and the selected DRUG_IMPORTER_PLUGIN supports it, the drug database is updated "
            "automatically in the background when a newer version is detected on the remote source. "
            "If False, updates must be triggered manually via the REST API or web client."
        ),
    )
    DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB: bool = Field(
        default=False,
        description=(
            "If True and the selected DRUG_IMPORTER_PLUGIN supports it, the REST API endpoint "
            "PUT /drug/db/update is enabled, allowing administrators to trigger a drug data update on demand. "
            "Has no effect if the plugin does not support manual updates."
        ),
    )

    DRUG_IMPORTER_BATCH_SIZE: int = Field(
        default=200000,
        description=(
            "Number of drug records processed per batch during a drug data import. "
            "Larger batches are faster but consume more memory. "
            "Reduce this value on low-memory systems to avoid out-of-memory errors during import."
        ),
        examples=[50000, 100000, 200000],
    )

    DRUG_IMPORTER_SOURCE_FTP_HOST: Optional[str] = Field(
        default=None,
        description=(
            "FTP hostname for the MMIPharmindex1_32 auto-update source. "
            "Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True."
        ),
        examples=["ftp.mmi-pharmindex.de"],
    )
    DRUG_IMPORTER_SOURCE_FTP_PORT: int = Field(
        default=21,
        description=(
            "FTP port for the MMIPharmindex1_32 update source. "
            "Only required when DRUG_IMPORTER_SOURCE_FTP_HOST is set. "
            "Defaults to the standard FTP port 21."
        ),
        examples=[21],
    )
    DRUG_IMPORTER_SOURCE_FTP_USER: Optional[str] = Field(
        default=None,
        description=(
            "FTP username to authenticate against the MMI Pharmindex FTP server. "
            "Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True."
        ),
    )
    DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC: int = Field(
        default=3600,
        description=(
            "Minimum time in seconds between consecutive checks of the remote drug data source for a newer version. "
            "Within the cooldown window, MedLog returns a cached result instead of querying the remote. "
            "Increase this to reduce FTP traffic; decrease it to detect updates more quickly."
        ),
        examples=[3600, 86400],
    )

    DRUG_IMPORTER_SOURCE_FTP_PASSWORD: Optional[SecretStr] = Field(
        default=None,
        description=(
            "FTP password to authenticate against the MMI Pharmindex FTP server. "
            "Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True."
        ),
    )
    DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR: str = Field(
        default="/tmp/medlog_drugdata",
        description=(
            "Local directory where downloaded drug data archives are stored before and during import. "
            "The directory must be writable by the MedLog process. "
            "Use a persistent path (not /tmp) to avoid re-downloading data on every restart."
        ),
        examples=["/tmp/medlog_drugdata", "/var/lib/medlog/drugdata"],
    )

    DRUG_SEARCHENGINE_CLASS: Literal["GenericSQLDrugSearch"] = Field(
        description=(
            "Selects the search engine backend used to answer drug search requests. "
            "Currently only 'GenericSQLDrugSearch' is available, which uses SQL-based full-text search. "
            "This field exists as an extension point for future alternative search backends."
        ),
        default="GenericSQLDrugSearch",
    )
    DRUG_TABLE_PROVISIONING_SOURCE_DIR: Optional[str] = Field(
        description=(
            "Path to a directory containing a pre-built drug dataset in the expected import format. "
            "If MedLog starts with an empty drug database, it will automatically import from this directory. "
            "Useful for offline deployments or pre-seeding a fresh database without a remote FTP source."
        ),
        default=str(
            Path(
                Path(__file__).parent.parent, "provisioning_data/dummy_drugset/20241126"
            ).absolute()
        ),
        examples=["/opt/medlog/drugdata/20241126", "/data/gkv_arzneimittel/latest"],
    )

    DRUG_DATA_IMPORT_MAX_ROWS: Optional[int] = Field(
        description=(
            "Limit the number of drug entries imported in a single run. "
            "Useful for debugging or demos where a full import would take too long. "
            "Set to None (default) to import all available entries."
        ),
        default=None,
        examples=[1000, 50000],
    )
    DRUG_DATA_IMPORT_ALLOWED_HOURS: Optional[List[int]] = Field(
        description=(
            "Restrict drug data imports to specific hours of the day (UTC, 0-23). "
            "Useful when multiple instances share a VM and you want to avoid simultaneous "
            "memory-intensive imports. E.g. [2, 3, 4, 5] allows imports only between 02:00 and 06:00 UTC. "
            "Null/unset means imports can start at any time."
        ),
        default=None,
        examples=[[2, 3, 4, 5], [0, 1, 2]],
    )

    EXPORT_CACHE_DIR: str = Field(
        default="./export_cache",
        description=(
            "Directory where completed export jobs store their output files (CSV, JSON, etc.). "
            "The directory is created automatically if it does not exist. "
            "Use an absolute path in production to avoid ambiguity."
        ),
        examples=["./export_cache", "/var/lib/medlog/exports"],
    )

    PROBAND_IDS_CASE_SENSETIVE: bool = Field(
        default=False,
        description=(
            "Controls whether proband (subject) IDs are treated as case-sensitive. "
            "If False (default), IDs '1A' and '1a' refer to the same proband. "
            "If True, they are treated as distinct probands. "
            "Note: the variable name contains a known typo ('SENSETIVE' instead of 'SENSITIVE') "
            "that is preserved for backward compatibility with existing deployments."
        ),
    )

    class SystemAnnouncement(BaseSettings):
        public: bool = Field(
            default=False,
            description="If True, this announcement is also shown to unauthenticated (not logged-in) users.",
        )
        type: Literal["info", "warning", "alert"] = Field(
            default="info",
            description="Visual style of the announcement banner: 'info' is neutral, 'warning' is yellow, 'alert' is red.",
        )
        message: str = Field(
            description="Text content of the announcement displayed in the web client.",
            examples=["Scheduled maintenance on 2025-01-15 from 02:00 to 04:00 UTC."],
        )

    SYSTEM_ANNOUNCEMENTS: List[SystemAnnouncement] = Field(
        default_factory=list,
        description=(
            "List of system-wide announcement banners displayed in the web client. "
            "Public announcements are shown to all visitors; non-public ones only to logged-in users. "
            "Pass as a JSON array string when setting via environment variable."
        ),
        examples=[
            """'[{"type": "info", "public": true, "message": "This is a public message"},{"type": "alert", "public": false, "message": "This is a non-public alert"}]'"""
        ],
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
