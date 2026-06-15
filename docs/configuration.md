# Configuration Reference

> [!NOTE]
> This file is auto-generated from [`MedLog/backend/medlogserver/config.py`](../MedLog/backend/medlogserver/config.py).
> Run `./build_config_docs.sh` from the repo root to regenerate it.

All settings are supplied via **environment variables** or a `.env` file placed at
`MedLog/backend/medlogserver/.env`. Nested settings use `__` as the delimiter
(e.g. `AUTH_OIDC_PROVIDERS__0__ENABLED`).

---

## `APP_NAME`

Display name of the application. Used in log output, session cookie names, and health-check responses.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"DZDMedLog"` |
| Environment variable | `APP_NAME` |

**Examples:**

*Example 1:*

```yaml
APP_NAME: DZDMedLog
```

*Example 2:*

```yaml
APP_NAME: MyMedLog
```

---

## `DOCKER_MODE`

Set to True when running inside Docker. Adjusts internal path resolution for provisioning files to use the Docker base directory defined by the MEDLOG_DOCKER_BASEDIR environment variable (default: /opt/medlog). The official Dockerfile sets this automatically via ENV DOCKER_MODE=1.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DOCKER_MODE` |

---

## `FRONTEND_FILES_DIR`

Path to the built Nuxt frontend output directory that contains index.html and all static assets. This directory is served by the backend as the web client. In development, run `npm run build` inside the frontend directory to generate it.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/frontend/.output/public"` |
| Environment variable | `FRONTEND_FILES_DIR` |

**Examples:**

*Example 1:*

```yaml
FRONTEND_FILES_DIR: /opt/medlog/frontend/.output/public
```

*Example 2:*

```yaml
FRONTEND_FILES_DIR: ./frontend/.output/public
```

---

## `LOG_LEVEL`

Verbosity of the application logger. DEBUG produces the most output; CRITICAL the least.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"INFO"` |
| Allowed values | `CRITICAL` · `ERROR` · `WARNING` · `INFO` · `DEBUG` |
| Environment variable | `LOG_LEVEL` |

---

## `LOG_DISABLE_COLORS`

If True, log output will have no ANSI color coding. Useful for log aggregators or terminals that do not support color escape codes.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `LOG_DISABLE_COLORS` |

---

## `DEMO_MODE`

If True, the application starts in demonstration mode: the database is seeded with sample data, and mandatory secrets such as SERVER_SESSION_SECRET are auto-generated if not provided. Do not use in production.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DEMO_MODE` |

---

## `DEBUG_SQL`

If True, the SQLAlchemy engine echoes all generated SQL statements to the log. Useful for debugging database queries.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DEBUG_SQL` |

---

## `SERVER_UVICORN_LOG_LEVEL`

Log level for the Uvicorn ASGI server. Accepts the same values as LOG_LEVEL. If not set, falls back to the value of LOG_LEVEL.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `SERVER_UVICORN_LOG_LEVEL` |

---

## `SERVER_LISTENING_PORT`

TCP port the Uvicorn server binds to and listens on.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `8888` |
| Environment variable | `SERVER_LISTENING_PORT` |

**Examples:**

*Example 1:*

```yaml
SERVER_LISTENING_PORT: 8888
```

*Example 2:*

```yaml
SERVER_LISTENING_PORT: 8080
```

*Example 3:*

```yaml
SERVER_LISTENING_PORT: 80
```

*Example 4:*

```yaml
SERVER_LISTENING_PORT: 443
```

---

## `SERVER_LISTENING_HOST`

Network interface the Uvicorn server binds to. Use '0.0.0.0' to accept connections on all interfaces (required in Docker). Use 'localhost' or '127.0.0.1' to restrict to the local machine only.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"localhost"` |
| Environment variable | `SERVER_LISTENING_HOST` |

**Examples:**

*Example 1:*

```yaml
SERVER_LISTENING_HOST: 0.0.0.0
```

*Example 2:*

```yaml
SERVER_LISTENING_HOST: localhost
```

*Example 3:*

```yaml
SERVER_LISTENING_HOST: 127.0.0.1
```

*Example 4:*

```yaml
SERVER_LISTENING_HOST: 176.16.8.123
```

---

## `SERVER_HOSTNAME`

External hostname or domain name under which the API is publicly reachable. Usually a fully-qualified domain name (FQDN) in production. If not set, the system hostname is used as a fallback. This value is used to build the server URL and OAuth redirect URIs.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Environment variable | `SERVER_HOSTNAME` |

**Examples:**

*Example 1:*

```yaml
SERVER_HOSTNAME: medlog.example.com
```

*Example 2:*

```yaml
SERVER_HOSTNAME: localhost
```

*Example 3:*

```yaml
SERVER_HOSTNAME: 10.0.0.5
```

---

## `SERVER_PROTOCOL`

Protocol used to reach the server from the outside. Automatic detection can fail behind reverse proxies that terminate TLS — set this explicitly to 'https' when serving over SSL.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"http"` |
| Allowed values | `http` · `https` |
| Environment variable | `SERVER_PROTOCOL` |

**Examples:**

*Example 1:*

```yaml
SERVER_PROTOCOL: http
```

*Example 2:*

```yaml
SERVER_PROTOCOL: https
```

---

## `SERVER_SESSION_SECRET`

Secret key used to sign and encrypt browser session cookies. Must be at least 64 characters long. Use a cryptographically random string and keep it private — rotating this value invalidates all active sessions.

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Constraints | MinLen(min_length=64) |
| Environment variable | `SERVER_SESSION_SECRET` |

---

## `SET_SESSION_COOKIE_SECURE`

If True, session cookies are only sent over HTTPS (the Secure flag is set). Set to False for local development over plain HTTP, but never in production.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `SET_SESSION_COOKIE_SECURE` |

---

## `CLIENT_URL`

URL where the web client is hosted. Usually the client is bundled with the server and this can be left unset — it is then derived automatically from SERVER_PROTOCOL, SERVER_HOSTNAME, and SERVER_LISTENING_PORT.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `CLIENT_URL` |

**Examples:**

*Example 1:*

```yaml
CLIENT_URL: https://medlog.example.com
```

*Example 2:*

```yaml
CLIENT_URL: http://localhost:8888
```

---

## `BRANDING_SUPPORT_EMAIL_ADDRESS`

Support email address displayed in the web client's help text. Leave unset to hide the support contact from the UI.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `BRANDING_SUPPORT_EMAIL_ADDRESS` |

**Examples:**

```yaml
BRANDING_SUPPORT_EMAIL_ADDRESS: support@example.com
```

---

## `SQL_DATABASE_URL`

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

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"sqlite+aiosqlite:///./../../../medlog.sqlite"` |
| Environment variable | `SQL_DATABASE_URL` |

**Examples:**

*Example 1:*

```yaml
SQL_DATABASE_URL: sqlite+aiosqlite:///local.db
```

*Example 2:*

```yaml
SQL_DATABASE_URL: sqlite+aiosqlite:////opt/data.db
```

*Example 3:*

```yaml
SQL_DATABASE_URL: 'sqlite+aiosqlite:///:memory:'
```

*Example 4:*

```yaml
SQL_DATABASE_URL: sqlite+aiosqlite:///./local2.sqlite
```

*Example 5:*

```yaml
SQL_DATABASE_URL: postgresql+psycopg://user:pass@localhost:5432/mydb
```

---

## `ADMIN_USER_NAME`

Username for the built-in administrator account created on first startup. Must be between 3 and 128 characters. This account always has full admin privileges regardless of role mappings.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"admin"` |
| Constraints | StringConstraints(strip_whitespace=True, to_upper=None, to_lower=None, strict=None, min_length=3, max_length=128, pattern=None) |
| Environment variable | `ADMIN_USER_NAME` |

**Examples:**

*Example 1:*

```yaml
ADMIN_USER_NAME: admin
```

*Example 2:*

```yaml
ADMIN_USER_NAME: medlog-admin
```

---

## `ADMIN_USER_PW`

Password for the built-in administrator account. Required unless DEMO_MODE is True (which sets it to 'adminadmin'). Choose a strong password for any non-demo deployment.

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Environment variable | `ADMIN_USER_PW` |

---

## `ADMIN_USER_EMAIL`

Email address for the built-in administrator account. Optional.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `ADMIN_USER_EMAIL` |

**Examples:**

```yaml
ADMIN_USER_EMAIL: admin@example.com
```

---

## `ADMIN_ROLE_NAME`

Name of the application-level administrator role. Users with this role have full access to all studies, user management, and system settings. Change this if your organisation uses a different naming convention, and update any OIDC ROLE_MAPPING accordingly.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"medlog-admin"` |
| Environment variable | `ADMIN_ROLE_NAME` |

**Examples:**

*Example 1:*

```yaml
ADMIN_ROLE_NAME: medlog-admin
```

*Example 2:*

```yaml
ADMIN_ROLE_NAME: app-admin
```

---

## `USERMANAGER_ROLE_NAME`

Name of the user-manager role. Users with this role can create, edit, and deactivate user accounts but cannot change system settings. Change this if your organisation uses a different naming convention, and update any OIDC ROLE_MAPPING accordingly.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"medlog-user-manager"` |
| Environment variable | `USERMANAGER_ROLE_NAME` |

**Examples:**

*Example 1:*

```yaml
USERMANAGER_ROLE_NAME: medlog-user-manager
```

*Example 2:*

```yaml
USERMANAGER_ROLE_NAME: user-admin
```

---

## `BACKGROUND_WORKER_START_IN_EXTRA_PROCESS`

If True, the background worker (responsible for drug data imports, provisioning, etc.) is launched automatically alongside the web server in a separate OS process. If False, the worker is not started — you must run a second instance manually using the dedicated worker entry point.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `BACKGROUND_WORKER_START_IN_EXTRA_PROCESS` |

---

## `BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN`

How many minutes to keep completed background job records in the database before deleting them. Keeping records for a while is useful for debugging. Set to None to retain finished job records indefinitely.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `1440` |
| Environment variable | `BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN` |

---

## `APP_PROVISIONING_DATA_YAML_FILES`

List of absolute paths to YAML files whose content is deserialized into MedLog models and loaded into the database on startup. Use this to pre-populate studies, users, or other entities in a fresh deployment. In DEMO_MODE a sample dataset is added automatically.

| Property | Value |
|---|---|
| Type | List of str |
| Required | No |
| Environment variable | `APP_PROVISIONING_DATA_YAML_FILES` |

**Examples:**

*Example 1:*

```yaml
APP_PROVISIONING_DATA_YAML_FILES:
- /opt/medlog/provisioning/my_study.yaml
```

*Example 2:*

```yaml
APP_PROVISIONING_DATA_YAML_FILES:
- ./provisioning_data/demo_data/single_study_demo_data.yaml
```

---

## `APP_PROVISIONING_DEFAULT_DATA_YAML_FILE`

Path to the built-in default data YAML file that is always loaded into the database on startup. It contains baseline background jobs, vocabularies, and system defaults required for the app to function. Under normal circumstances you do not need to change this. To provision custom data such as studies, use APP_PROVISIONING_DATA_YAML_FILES instead.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/backend/medlogserver/default_data.yaml"` |
| Environment variable | `APP_PROVISIONING_DEFAULT_DATA_YAML_FILE` |

---

## `APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT`

If True, all users can access all newly created studies and edit interviews without being explicitly granted permissions. Useful for small, trusted deployments where fine-grained access control is not needed. Has no effect on existing studies — only newly created studies inherit this default.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT` |

---

## `AUTH_BASIC_LOGIN_IS_ENABLED`

Allow users with locally stored credentials (username + password) to log in. Disable when authentication is handled entirely by an external OIDC provider and you want to prevent direct password-based logins.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `AUTH_BASIC_LOGIN_IS_ENABLED` |

---

## `AUTH_BASIC_USER_DB_REGISTER_ENABLED`

NOT YET IMPLEMENTED. Placeholder for a future self-registration feature. Self-registration of users is currently not supported; this field is locked to False and cannot be enabled.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `false` |
| Allowed values | `False` |
| Environment variable | `AUTH_BASIC_USER_DB_REGISTER_ENABLED` |

---

## `API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES`

How many minutes an API access token remains valid after it is issued. Applies to tokens created via login or the token management endpoint. Set to None for tokens that never expire (not recommended for production).

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `10080` |
| Environment variable | `API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES` |

**Examples:**

*Example 1:*

```yaml
API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES: 60
```

*Example 2:*

```yaml
API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES: 1440
```

*Example 3:*

```yaml
API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES: 10080
```

---

## `AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS`

NOT YET IMPLEMENTED. Placeholder for a future cross-provider user-merge feature. When implemented: if True, a user authenticating via a different provider but with the same username as an existing account will be merged into that account. If False, a duplicate username from a second provider will raise an error. Currently has no effect.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS` |

---

## `AUTH_OIDC_TOKEN_STORAGE_SECRET`

Secret string used to encrypt OIDC access and refresh tokens before storing them in the database. Required when AUTH_OIDC_PROVIDERS is non-empty — provide a long random string and keep it stable across restarts. Rotating this value invalidates all stored OIDC tokens and forces all OIDC users to re-authenticate. If no OIDC providers are configured, this value is auto-generated (tokens are never stored in that case).

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `AUTH_OIDC_TOKEN_STORAGE_SECRET` |

---

## `AUTH_OIDC_PROVIDERS`

List of OpenID Connect (OIDC) provider configurations for federated authentication. Each entry represents one external identity provider (e.g. Keycloak, Azure AD). Leave empty to use only local username/password login.

| Property | Value |
|---|---|
| Type | List of Object (OpenIDConnectProvider) |
| Required | No |
| Environment variable | `AUTH_OIDC_PROVIDERS` |

---

### `AUTH_OIDC_PROVIDERS[*]` — `OpenIDConnectProvider` schema

---

### `AUTH_OIDC_PROVIDERS[*].ENABLED`

Set to True to activate this OIDC provider. If False, the provider is ignored at startup.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__ENABLED` |

---

### `AUTH_OIDC_PROVIDERS[*].PROVIDER_DISPLAY_NAME`

Display name shown on the login page for this provider. Must be unique across all configured OIDC providers.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"My OpenID Connect Login"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__PROVIDER_DISPLAY_NAME` |

**Examples:**

*Example 1:*

```yaml
PROVIDER_DISPLAY_NAME: Keycloak
```

*Example 2:*

```yaml
PROVIDER_DISPLAY_NAME: Azure AD
```

*Example 3:*

```yaml
PROVIDER_DISPLAY_NAME: Google
```

---

### `AUTH_OIDC_PROVIDERS[*].AUTO_LOGIN`

If True, the client immediately redirects to this provider's login page instead of showing MedLog's own login form. Only meaningful when exactly one OIDC provider is configured.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__AUTO_LOGIN` |

---

### `AUTH_OIDC_PROVIDERS[*].CONFIGURATION_ENDPOINT`

OpenID Connect discovery document URL of the provider (the 'well-known' endpoint). MedLog fetches the authorization, token, and JWKS endpoints from this URL automatically.

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CONFIGURATION_ENDPOINT` |

**Examples:**

*Example 1:*

```yaml
CONFIGURATION_ENDPOINT: https://keycloak.example.com/realms/myrealm/.well-known/openid-configuration
```

*Example 2:*

```yaml
CONFIGURATION_ENDPOINT: https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration
```

---

### `AUTH_OIDC_PROVIDERS[*].CLIENT_ID`

Client ID registered for MedLog in the OIDC provider.

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CLIENT_ID` |

**Examples:**

*Example 1:*

```yaml
CLIENT_ID: medlog-client
```

*Example 2:*

```yaml
CLIENT_ID: abc123xyz
```

---

### `AUTH_OIDC_PROVIDERS[*].CLIENT_SECRET`

Client secret registered for MedLog in the OIDC provider. Keep this value private.

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CLIENT_SECRET` |

---

### `AUTH_OIDC_PROVIDERS[*].SCOPES`

OAuth2/OIDC scopes to request from the provider. The 'offline_access' scope requests a refresh token, which keeps the session alive without requiring the user to log in again after the access token expires. Remove it if your provider does not support refresh tokens.

| Property | Value |
|---|---|
| Type | List of str |
| Required | No |
| Default | `["openid", "profile", "email", "offline_access"]` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__SCOPES` |

**Examples:**

```yaml
SCOPES:
- openid
- profile
- email
- offline_access
```

---

### `AUTH_OIDC_PROVIDERS[*].USER_NAME_ATTRIBUTE`

Claim in the OIDC ID token that contains the unique, stable username used as the MedLog account identifier. This value must be unique per user and must not change over time.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"preferred_username"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_NAME_ATTRIBUTE` |

**Examples:**

*Example 1:*

```yaml
USER_NAME_ATTRIBUTE: preferred_username
```

*Example 2:*

```yaml
USER_NAME_ATTRIBUTE: sub
```

*Example 3:*

```yaml
USER_NAME_ATTRIBUTE: upn
```

---

### `AUTH_OIDC_PROVIDERS[*].USER_DISPLAY_NAME_ATTRIBUTE`

Claim in the OIDC ID token used as the user's display name in the MedLog UI. Note: the default 'display_name' is not a standard OIDC claim — common alternatives are 'name' or 'given_name'.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"display_name"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_DISPLAY_NAME_ATTRIBUTE` |

**Examples:**

*Example 1:*

```yaml
USER_DISPLAY_NAME_ATTRIBUTE: display_name
```

*Example 2:*

```yaml
USER_DISPLAY_NAME_ATTRIBUTE: name
```

*Example 3:*

```yaml
USER_DISPLAY_NAME_ATTRIBUTE: given_name
```

---

### `AUTH_OIDC_PROVIDERS[*].USER_MAIL_ATTRIBUTE`

Claim in the OIDC ID token that contains the user's email address.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"email"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_MAIL_ATTRIBUTE` |

**Examples:**

```yaml
USER_MAIL_ATTRIBUTE: email
```

---

### `AUTH_OIDC_PROVIDERS[*].USER_GROUPS_ATTRIBUTE`

Claim in the OIDC ID token that contains the list of groups the user belongs to. Used for ROLE_MAPPING and STUDY_PERMISSION_MAPPING. The attribute name varies by provider — common values are 'groups' or 'roles'.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"groups"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_GROUPS_ATTRIBUTE` |

**Examples:**

*Example 1:*

```yaml
USER_GROUPS_ATTRIBUTE: groups
```

*Example 2:*

```yaml
USER_GROUPS_ATTRIBUTE: roles
```

*Example 3:*

```yaml
USER_GROUPS_ATTRIBUTE: cognito:groups
```

---

### `AUTH_OIDC_PROVIDERS[*].AUTO_CREATE_AUTHORIZED_USER`

If True, a new MedLog user account is created automatically on the first login via this OIDC provider when no matching local account exists. If False, only users that already have a local account can log in via OIDC.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__AUTO_CREATE_AUTHORIZED_USER` |

---

### `AUTH_OIDC_PROVIDERS[*].AUTO_CREATE_STUDY_FROM_MAPPING`

If a study referenced in STUDY_PERMISSION_MAPPING does not exist in the database, create it automatically on the first OIDC login that triggers the mapping. Useful when studies are managed entirely via the OIDC configuration. Default is False: missing studies produce a warning and are skipped.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__AUTO_CREATE_STUDY_FROM_MAPPING` |

---

### `AUTH_OIDC_PROVIDERS[*].PREFIX_USERNAME_WITH_PROVIDER_SLUG`

If True, the provider's URL-safe slug is prepended to usernames from this provider (e.g. 'keycloak__john.doe'). Prevents username collisions when multiple OIDC providers are configured and users from different providers could share the same username.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__PREFIX_USERNAME_WITH_PROVIDER_SLUG` |

---

### `AUTH_OIDC_PROVIDERS[*].ROLE_MAPPING`

Maps OIDC group names to MedLog application roles. Each key is an OIDC group name; the value is a list of MedLog role names to assign. Available built-in roles are defined by ADMIN_ROLE_NAME and USERMANAGER_ROLE_NAME.

| Property | Value |
|---|---|
| Type | Dictionary of (str, List of str) |
| Required | No |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__ROLE_MAPPING` |

**Examples:**

```yaml
ROLE_MAPPING:
  oidc_appadmins:
  - medlog-admin
  oidc_usermgrs:
  - medlog-user-manager
```

---

### `AUTH_OIDC_PROVIDERS[*].STUDY_PERMISSION_MAPPING`

Maps OIDC group membership to per-study permissions. Top-level key is the study name; each inner key is an OIDC group name; the value is a list of permissions to grant. Valid permissions: is_study_interviewer, is_study_viewer, is_study_admin.

| Property | Value |
|---|---|
| Type | Dictionary of (str, Dictionary of (str, List of str)) |
| Required | No |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__STUDY_PERMISSION_MAPPING` |

**Examples:**

```yaml
STUDY_PERMISSION_MAPPING: "{\n                            \"MyStudyName\": {\n   \
  \                             \"medlog-oidc-group-interviewer\": [\n           \
  \                     \"is_study_interviewer\"\n                               \
  \ ],\n                                \"medlog-oidc-group-exporter\": [\n      \
  \                          \"is_study_viewer\"\n                               \
  \ ],\n                                \"medlog-oidc-group-admin\": [\n         \
  \                       \"is_study_admin\"\n                                ],\n\
  \                                \"medlog-oidc-group-user-manager\": [\n       \
  \                         \"is_study_admin\"\n                                ]\n\
  \                            }\n                            }\n"
```

---

## `DRUG_IMPORTER_PLUGIN`

Selects the drug data importer plugin. 'DummyDrugImporterV1' uses a small built-in sample dataset, suitable for development and demos. 'MMIPharmindex1_32' imports from the MMI Pharmindex format (version 1.32), used with German GKV Arzneimittelverzeichnis data.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"DummyDrugImporterV1"` |
| Allowed values | `MMIPharmindex1_32` · `DummyDrugImporterV1` |
| Environment variable | `DRUG_IMPORTER_PLUGIN` |

**Examples:**

*Example 1:*

```yaml
DRUG_IMPORTER_PLUGIN: DummyDrugImporterV1
```

*Example 2:*

```yaml
DRUG_IMPORTER_PLUGIN: MMIPharmindex1_32
```

---

## `DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB`

If True and the selected DRUG_IMPORTER_PLUGIN supports it, the drug database is updated automatically in the background when a newer version is detected on the remote source. If False, updates must be triggered manually via the REST API or web client.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB` |

---

## `DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB`

If True and the selected DRUG_IMPORTER_PLUGIN supports it, the REST API endpoint PUT /drug/db/update is enabled, allowing administrators to trigger a drug data update on demand. Has no effect if the plugin does not support manual updates.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB` |

---

## `DRUG_IMPORTER_BATCH_SIZE`

Number of drug records processed per batch during a drug data import. Larger batches are faster but consume more memory. Reduce this value on low-memory systems to avoid out-of-memory errors during import.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `200000` |
| Environment variable | `DRUG_IMPORTER_BATCH_SIZE` |

**Examples:**

*Example 1:*

```yaml
DRUG_IMPORTER_BATCH_SIZE: 50000
```

*Example 2:*

```yaml
DRUG_IMPORTER_BATCH_SIZE: 100000
```

*Example 3:*

```yaml
DRUG_IMPORTER_BATCH_SIZE: 200000
```

---

## `DRUG_IMPORTER_SOURCE_FTP_HOST`

FTP hostname for the MMIPharmindex1_32 auto-update source. Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_HOST` |

**Examples:**

```yaml
DRUG_IMPORTER_SOURCE_FTP_HOST: ftp.mmi-pharmindex.de
```

---

## `DRUG_IMPORTER_SOURCE_FTP_PORT`

FTP port for the MMIPharmindex1_32 update source. Only required when DRUG_IMPORTER_SOURCE_FTP_HOST is set. Defaults to the standard FTP port 21.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `21` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_PORT` |

**Examples:**

```yaml
DRUG_IMPORTER_SOURCE_FTP_PORT: 21
```

---

## `DRUG_IMPORTER_SOURCE_FTP_USER`

FTP username to authenticate against the MMI Pharmindex FTP server. Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_USER` |

---

## `DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC`

Minimum time in seconds between consecutive checks of the remote drug data source for a newer version. Within the cooldown window, MedLog returns a cached result instead of querying the remote. Increase this to reduce FTP traffic; decrease it to detect updates more quickly.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `3600` |
| Environment variable | `DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC` |

**Examples:**

*Example 1:*

```yaml
DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC: 3600
```

*Example 2:*

```yaml
DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC: 86400
```

---

## `DRUG_IMPORTER_SOURCE_FTP_PASSWORD`

FTP password to authenticate against the MMI Pharmindex FTP server. Only required when DRUG_IMPORTER_PLUGIN='MMIPharmindex1_32' and DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB=True.

| Property | Value |
|---|---|
| Type | Object |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_PASSWORD` |

---

## `DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR`

Local directory where downloaded drug data archives are stored before and during import. The directory must be writable by the MedLog process. Use a persistent path (not /tmp) to avoid re-downloading data on every restart.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"/tmp/medlog_drugdata"` |
| Environment variable | `DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR` |

**Examples:**

*Example 1:*

```yaml
DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR: /tmp/medlog_drugdata
```

*Example 2:*

```yaml
DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR: /var/lib/medlog/drugdata
```

---

## `DRUG_SEARCHENGINE_CLASS`

Selects the search engine backend used to answer drug search requests. Currently only 'GenericSQLDrugSearch' is available, which uses SQL-based full-text search. This field exists as an extension point for future alternative search backends.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"GenericSQLDrugSearch"` |
| Allowed values | `GenericSQLDrugSearch` |
| Environment variable | `DRUG_SEARCHENGINE_CLASS` |

---

## `DRUG_TABLE_PROVISIONING_SOURCE_DIR`

Path to a directory containing a pre-built drug dataset in the expected import format. If MedLog starts with an empty drug database, it will automatically import from this directory. Useful for offline deployments or pre-seeding a fresh database without a remote FTP source.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/backend/provisioning_data/dummy_drugset/20241126"` |
| Environment variable | `DRUG_TABLE_PROVISIONING_SOURCE_DIR` |

**Examples:**

*Example 1:*

```yaml
DRUG_TABLE_PROVISIONING_SOURCE_DIR: /opt/medlog/drugdata/20241126
```

*Example 2:*

```yaml
DRUG_TABLE_PROVISIONING_SOURCE_DIR: /data/gkv_arzneimittel/latest
```

---

## `DRUG_DATA_IMPORT_MAX_ROWS`

Limit the number of drug entries imported in a single run. Useful for debugging or demos where a full import would take too long. Set to None (default) to import all available entries.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_DATA_IMPORT_MAX_ROWS` |

**Examples:**

*Example 1:*

```yaml
DRUG_DATA_IMPORT_MAX_ROWS: 1000
```

*Example 2:*

```yaml
DRUG_DATA_IMPORT_MAX_ROWS: 50000
```

---

## `DRUG_DATA_IMPORT_ALLOWED_HOURS`

Restrict drug data imports to specific hours of the day (UTC, 0-23). Useful when multiple instances share a VM and you want to avoid simultaneous memory-intensive imports. E.g. [2, 3, 4, 5] allows imports only between 02:00 and 06:00 UTC. Null/unset means imports can start at any time.

| Property | Value |
|---|---|
| Type | List of int |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_DATA_IMPORT_ALLOWED_HOURS` |

**Examples:**

*Example 1:*

```yaml
DRUG_DATA_IMPORT_ALLOWED_HOURS:
- 2
- 3
- 4
- 5
```

*Example 2:*

```yaml
DRUG_DATA_IMPORT_ALLOWED_HOURS:
- 0
- 1
- 2
```

---

## `EXPORT_CACHE_DIR`

Directory where completed export jobs store their output files (CSV, JSON, etc.). The directory is created automatically if it does not exist. Use an absolute path in production to avoid ambiguity.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"./export_cache"` |
| Environment variable | `EXPORT_CACHE_DIR` |

**Examples:**

*Example 1:*

```yaml
EXPORT_CACHE_DIR: ./export_cache
```

*Example 2:*

```yaml
EXPORT_CACHE_DIR: /var/lib/medlog/exports
```

---

## `PROBAND_IDS_CASE_SENSETIVE`

Controls whether proband (subject) IDs are treated as case-sensitive. If False (default), IDs '1A' and '1a' refer to the same proband. If True, they are treated as distinct probands. Note: the variable name contains a known typo ('SENSETIVE' instead of 'SENSITIVE') that is preserved for backward compatibility with existing deployments.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `PROBAND_IDS_CASE_SENSETIVE` |

---

## `SYSTEM_ANNOUNCEMENTS`

List of system-wide announcement banners displayed in the web client. Public announcements are shown to all visitors; non-public ones only to logged-in users. Pass as a JSON array string when setting via environment variable.

| Property | Value |
|---|---|
| Type | List of Object (SystemAnnouncement) |
| Required | No |
| Environment variable | `SYSTEM_ANNOUNCEMENTS` |

**Examples:**

```yaml
SYSTEM_ANNOUNCEMENTS: '''[{"type": "info", "public": true, "message": "This is a public
  message"},{"type": "alert", "public": false, "message": "This is a non-public alert"}]'''
```

---

### `SYSTEM_ANNOUNCEMENTS[*]` — `SystemAnnouncement` schema

---

### `SYSTEM_ANNOUNCEMENTS[*].public`

If True, this announcement is also shown to unauthenticated (not logged-in) users.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__PUBLIC` |

---

### `SYSTEM_ANNOUNCEMENTS[*].type`

Visual style of the announcement banner: 'info' is neutral, 'warning' is yellow, 'alert' is red.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"info"` |
| Allowed values | `info` · `warning` · `alert` |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__TYPE` |

---

### `SYSTEM_ANNOUNCEMENTS[*].message`

Text content of the announcement displayed in the web client.

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__MESSAGE` |

**Examples:**

```yaml
message: Scheduled maintenance on 2025-01-15 from 02:00 to 04:00 UTC.
```

---
