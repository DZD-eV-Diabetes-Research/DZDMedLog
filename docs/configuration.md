# Configuration Reference

> [!NOTE]
> This file is auto-generated from [`MedLog/backend/medlogserver/config.py`](../MedLog/backend/medlogserver/config.py).
> Run `./build_config_docs.sh` from the repo root to regenerate it.

All settings are supplied via **environment variables** or a `.env` file placed at
`MedLog/backend/medlogserver/.env`. Nested settings use `__` as the delimiter
(e.g. `AUTH_OIDC_PROVIDERS__0__ENABLED`).

---

## `APP_NAME`

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"DZDMedLog"` |
| Environment variable | `APP_NAME` |

---

## `DOCKER_MODE`

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DOCKER_MODE` |

---

## `FRONTEND_FILES_DIR`

The generated nuxt dir that contains index.html,...

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/frontend/.output/public"` |
| Environment variable | `FRONTEND_FILES_DIR` |

---

## `LOG_LEVEL`

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"INFO"` |
| Allowed values | `CRITICAL` · `ERROR` · `WARNING` · `INFO` · `DEBUG` |
| Environment variable | `LOG_LEVEL` |

---

## `LOG_DISABLE_COLORS`

If set to true, there will be color coding in the logs

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `LOG_DISABLE_COLORS` |

---

## `DEMO_MODE`

If set to yes, the database will initiate with some demo data and most config mandatory config vars, like crypto secrets will be set to something random.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DEMO_MODE` |

---

## `DEBUG_SQL`

If set to true, the sql engine will print out all sql queries to the log.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DEBUG_SQL` |

---

## `SERVER_UVICORN_LOG_LEVEL`

The log level of the uvicorn server. If not defined it will be the same as LOG_LEVEL.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `SERVER_UVICORN_LOG_LEVEL` |

---

## `SERVER_LISTENING_PORT`

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `8888` |
| Environment variable | `SERVER_LISTENING_PORT` |

---

## `SERVER_LISTENING_HOST`

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

The (external) hostname/domainname where the API is available. Usally a FQDN in productive systems. If not defined, it will be automatically detected based on the hostname.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Environment variable | `SERVER_HOSTNAME` |

**Examples:**

*Example 1:*

```yaml
SERVER_HOSTNAME: mydomain.com
```

*Example 2:*

```yaml
SERVER_HOSTNAME: localhost:8008
```

---

## `SERVER_PROTOCOL`

The protocol detection can fail in certain reverse proxy situations. This option allows you to manually override the automatic detection

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"http"` |
| Allowed values | `http` · `https` |
| Environment variable | `SERVER_PROTOCOL` |

---

## `SERVER_SESSION_SECRET`

The secret used to encrypt session state. Provide a long random string.

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Constraints | MinLen(min_length=64) |
| Environment variable | `SERVER_SESSION_SECRET` |

---

## `SET_SESSION_COOKIE_SECURE`

if you want to run the app on a non ssl connection set this to false. e.g for local development.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `SET_SESSION_COOKIE_SECURE` |

---

## `CLIENT_URL`

The URL where the client is hosted. Usualy it comes with the server

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `CLIENT_URL` |

---

## `BRANDING_SUPPORT_EMAIL_ADDRESS`

The email address the webclient will show in the help text to point to user support.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `BRANDING_SUPPORT_EMAIL_ADDRESS` |

---

## `SQL_DATABASE_URL`

The database URL for the application. Only SQLite (via `sqlite+aiosqlite`)
and PostgreSQL (via `postgresql+psycopg`) URLs are supported.

`sqlite+aiosqlite` and `postgresql+psycopg` specify the async DB drivers used
by SQLAlchemy’s async engine. They are required so the application can run
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

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"admin"` |
| Constraints | StringConstraints(strip_whitespace=True, to_upper=None, to_lower=None, strict=None, min_length=3, max_length=128, pattern=None) |
| Environment variable | `ADMIN_USER_NAME` |

---

## `ADMIN_USER_PW`

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Environment variable | `ADMIN_USER_PW` |

---

## `ADMIN_USER_EMAIL`

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `ADMIN_USER_EMAIL` |

---

## `ADMIN_ROLE_NAME`

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"medlog-admin"` |
| Environment variable | `ADMIN_ROLE_NAME` |

---

## `USERMANAGER_ROLE_NAME`

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"medlog-user-manager"` |
| Environment variable | `USERMANAGER_ROLE_NAME` |

---

## `BACKGROUND_WORKER_START_IN_EXTRA_PROCESS`

If set to True the background service will start in an extra Process next to the webserver. If set to False, the backgroundworker will not run. You have to setup an extra instance of the worker.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `BACKGROUND_WORKER_START_IN_EXTRA_PROCESS` |

---

## `BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN`

Jobs like the import of new Arzneimitteldata, are queued in the database. For debuging porposes you might want to keep the job info in the queue table for a while. If set to 'None', finished jobs will remain in the DB forever.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `1440` |
| Environment variable | `BACKGROUND_WORKER_TIDY_UP_FINISHED_JOBS_AFTER_N_MIN` |

---

## `APP_PROVISIONING_DATA_YAML_FILES`

A list if yaml files to serialize and load into MedLog models and into the DB 

| Property | Value |
|---|---|
| Type | List of str |
| Required | No |
| Environment variable | `APP_PROVISIONING_DATA_YAML_FILES` |

---

## `APP_PROVISIONING_DEFAULT_DATA_YAML_FILE`

Default data like some background jobs and vocabulary that is always loaded in the database. Under normal circustances this is nothing you need to changed. if you need to provision data like a Study into the database use the APP_PROVISIONING_DATA_YAML_FILES param.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/backend/medlogserver/default_data.yaml"` |
| Environment variable | `APP_PROVISIONING_DEFAULT_DATA_YAML_FILE` |

---

## `APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT`

If set to True; all user can access all new created studies, edit settings and create and edit interviews. This may be utile on small instances with a trusted userbase where user management is not wanted/needed.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `APP_STUDY_PERMISSION_SYSTEM_DISABLED_BY_DEFAULT` |

---

## `AUTH_BASIC_LOGIN_IS_ENABLED`

Local DB users are enabled to login. You could disable this, when having an external OIDC provider.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `AUTH_BASIC_LOGIN_IS_ENABLED` |

---

## `AUTH_BASIC_USER_DB_REGISTER_ENABLED`

Self registration of users is not supported yet.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `false` |
| Allowed values | `False` |
| Environment variable | `AUTH_BASIC_USER_DB_REGISTER_ENABLED` |

---

## `API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES`

If an api access token was created (on login or in token management) they should expire after this time.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `10080` |
| Environment variable | `API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES` |

---

## `AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS`

OPTION NOT IMPLEMENTED YET! If true, users from different providers with the same name are merged into one user. If false users with same name will cause an error. 

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `true` |
| Environment variable | `AUTH_MERGE_USERS_FROM_DIFFERENT_PROVIDERS` |

---

## `AUTH_OIDC_TOKEN_STORAGE_SECRET`

Random string to encrypt the oidc access and refresh token for storing it in the database.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"placeholder_until_todo_see_below"` |
| Environment variable | `AUTH_OIDC_TOKEN_STORAGE_SECRET` |

---

## `AUTH_OIDC_PROVIDERS`

Configure additional/alternative OpenID Connect (OIDC) provider settings for integrating.

| Property | Value |
|---|---|
| Type | List of Object (OpenIDConnectProvider) |
| Required | No |
| Environment variable | `AUTH_OIDC_PROVIDERS` |

---

### `AUTH_OIDC_PROVIDERS[*]` — `OpenIDConnectProvider` schema

---

### `AUTH_OIDC_PROVIDERS[*].ENABLED`

Is the provider enabled

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__ENABLED` |

---

### `AUTH_OIDC_PROVIDERS[*].PROVIDER_DISPLAY_NAME`

The unique name of the OpenID Connect provider shown to the user.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"My OpenID Connect Login"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__PROVIDER_DISPLAY_NAME` |

---

### `AUTH_OIDC_PROVIDERS[*].AUTO_LOGIN`

If set to true, the client will try to immediatly redirect to this provider instead of showing the login page.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__AUTO_LOGIN` |

---

### `AUTH_OIDC_PROVIDERS[*].CONFIGURATION_ENDPOINT`

The discovery endpoint of the OpenID Connect provider.

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CONFIGURATION_ENDPOINT` |

---

### `AUTH_OIDC_PROVIDERS[*].CLIENT_ID`

The client id of the OpenID Connect provider.

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CLIENT_ID` |

---

### `AUTH_OIDC_PROVIDERS[*].CLIENT_SECRET`

The client secret of the OpenID Connect provider.

| Property | Value |
|---|---|
| Type | Object |
| Required | **Yes** |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__CLIENT_SECRET` |

---

### `AUTH_OIDC_PROVIDERS[*].SCOPES`

hint: Scope `offline_access` is needed to get not only a access token but also a refresh token. This enables the application to keep the session alive without the need for the user to relogin.

| Property | Value |
|---|---|
| Type | List of str |
| Required | No |
| Default | `["openid", "profile", "email", "offline_access"]` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__SCOPES` |

---

### `AUTH_OIDC_PROVIDERS[*].USER_NAME_ATTRIBUTE`

The attribute of the OpenID Connect provider that contains a unique id of the user.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"preferred_username"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_NAME_ATTRIBUTE` |

---

### `AUTH_OIDC_PROVIDERS[*].USER_DISPLAY_NAME_ATTRIBUTE`

The attribute of the OpenID Connect provider that contains the display name of the user.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"display_name"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_DISPLAY_NAME_ATTRIBUTE` |

---

### `AUTH_OIDC_PROVIDERS[*].USER_MAIL_ATTRIBUTE`

The attribute of the OpenID Connect provider that contains a unique id of the user.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"email"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_MAIL_ATTRIBUTE` |

---

### `AUTH_OIDC_PROVIDERS[*].USER_GROUPS_ATTRIBUTE`

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"groups"` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__USER_GROUPS_ATTRIBUTE` |

---

### `AUTH_OIDC_PROVIDERS[*].AUTO_CREATE_AUTHORIZED_USER`

If a user does not exists in the local database, create the user on first authorization via the OIDC Provider.

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

To prevent username colliction between different OIDC providers, we can prefix the usernames from the OIDC provider with it slug.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__PREFIX_USERNAME_WITH_PROVIDER_SLUG` |

---

### `AUTH_OIDC_PROVIDERS[*].ROLE_MAPPING`

A JSON to map OIDC groups to DZDMedLog Roles. e.g. `{"oidc_appadmins":["medlog-user-manager"],"admins":["medlog-admins"]}`

| Property | Value |
|---|---|
| Type | Dictionary of (str, List of str) |
| Required | No |
| Environment variable | `AUTH_OIDC_PROVIDERS[*]__ROLE_MAPPING` |

---

### `AUTH_OIDC_PROVIDERS[*].STUDY_PERMISSION_MAPPING`

Map study permissions to membership in OIDC groups. Allowed permissions are is_study_interviewer, is_study_viewer, is_study_admin

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

Depending on the drug database that is used, we can define an importer.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"DummyDrugImporterV1"` |
| Allowed values | `MMIPharmindex1_32` · `DummyDrugImporterV1` |
| Environment variable | `DRUG_IMPORTER_PLUGIN` |

---

## `DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB`

If the drug importer plugin, does support it, the drug DB will be updated automaticly. Otherwise it must be manually triggered via the RestApi/WebClient

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DRUG_IMPORTER_AUTO_UPDATE_DRUG_DB` |

---

## `DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB`

If the drug importer plugin, does support it, does the REST-API/WebClient allow the usage of the endpoint PUT-`/drug/db/update` to force an update of the drug data

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB` |

---

## `DRUG_IMPORTER_BATCH_SIZE`

If the drug import supports batching, this is the size per batch. The trade of are some speed bumps, while drug importing, versus memory consumption. On a low memory machine decrease this value.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `200000` |
| Environment variable | `DRUG_IMPORTER_BATCH_SIZE` |

---

## `DRUG_IMPORTER_SOURCE_FTP_HOST`

When using MMIPharmindex1_32 auto updater, this is the FTP host to check for available datasets.

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_HOST` |

---

## `DRUG_IMPORTER_SOURCE_FTP_PORT`

When using MMIPharmindex1_32 auto updater, this is the FTP port to connect to `DRUG_IMPORTER_SOURCE_FTP_HOST`.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `21` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_PORT` |

---

## `DRUG_IMPORTER_SOURCE_FTP_USER`

When using MMIPharmindex1_32 auto updater, authorize with this username against the MMI Pharmindex FTP Server 

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_USER` |

---

## `DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC`

What time should we wait until we re-check the remote drug data source if there is an update available. If queried in the cooldown time medlog will return a chached value.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `3600` |
| Environment variable | `DRUG_IMPORTER_REMOTE_VERSION_CHECK_COOLDOWN_TIME_SEC` |

---

## `DRUG_IMPORTER_SOURCE_FTP_PASSWORD`

When using MMIPharmindex1_32 auto updater, authorize with this password against the MMI Pharmindex FTP Server 

| Property | Value |
|---|---|
| Type | Object |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_IMPORTER_SOURCE_FTP_PASSWORD` |

---

## `DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR`

A directory for storing downloaded drug data sets

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"/tmp/medlog_drugdata"` |
| Environment variable | `DRUG_IMPORTER_DRUG_DATA_SETS_STORAGE_DIR` |

---

## `DRUG_SEARCHENGINE_CLASS`

The search engine used in the background to answer drug search requests.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"GenericSQLDrugSearch"` |
| Allowed values | `GenericSQLDrugSearch` |
| Environment variable | `DRUG_SEARCHENGINE_CLASS` |

---

## `DRUG_TABLE_PROVISIONING_SOURCE_DIR`

If MedLog is booted with an empty drug database, it will check if a source data set of the GKV Arzneimittel Index is located in this dir

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"MedLog/backend/provisioning_data/dummy_drugset/20241126"` |
| Environment variable | `DRUG_TABLE_PROVISIONING_SOURCE_DIR` |

---

## `DRUG_DATA_IMPORT_MAX_ROWS`

For debuging or demo purposes you can limit the amount of drug entries that are parsed and import while the drug importer runs. This speeds up the import process massivly but you will not have all drug entries.

| Property | Value |
|---|---|
| Type | int |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_DATA_IMPORT_MAX_ROWS` |

---

## `DRUG_DATA_IMPORT_ALLOWED_HOURS`

Restrict drug data imports to specific hours of the day (UTC, 0-23). Useful when multiple instances share a VM and you want to avoid simultaneous memory-intensive imports. E.g. [2, 3, 4, 5] allows imports only between 02:00 and 06:00 UTC. Null/unset means imports can start at any time.

| Property | Value |
|---|---|
| Type | List of int |
| Required | No |
| Default | `null` |
| Environment variable | `DRUG_DATA_IMPORT_ALLOWED_HOURS` |

---

## `EXPORT_CACHE_DIR`

The directory to store the result of export jobs (CSV files, JSON files,...).

| Property | Value |
|---|---|
| Type | str |
| Required | No |
| Default | `"./export_cache"` |
| Environment variable | `EXPORT_CACHE_DIR` |

---

## `PROBAND_IDS_CASE_SENSETIVE`

If set to true a proband with the ID '1A' will be different from '1a'.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `PROBAND_IDS_CASE_SENSETIVE` |

---

## `SYSTEM_ANNOUNCEMENTS`

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

Should this announcement be shown to non logged in users as well.

| Property | Value |
|---|---|
| Type | bool |
| Required | No |
| Default | `false` |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__PUBLIC` |

---

### `SYSTEM_ANNOUNCEMENTS[*].type`

Which type the announcement is.

| Property | Value |
|---|---|
| Type | Enum |
| Required | No |
| Default | `"info"` |
| Allowed values | `info` · `warning` · `alert` |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__TYPE` |

---

### `SYSTEM_ANNOUNCEMENTS[*].message`

| Property | Value |
|---|---|
| Type | str |
| Required | **Yes** |
| Environment variable | `SYSTEM_ANNOUNCEMENTS[*]__MESSAGE` |

---
