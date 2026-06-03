# Application Logic

## Core Concepts

DZDMedLog is built around five nested entities. Understanding how they relate to each other is the key to understanding the whole application.

```
Study
 └── Event  (a visit / timepoint, e.g. "Baseline", "Month-6")
      └── Interview  (one session per proband per event)
           └── Intake  (one medication entry per interview)
                └── Drug  (looked up from the drug database)
```

### Study

A **Study** is the top-level container. All data lives inside a study. An instance of MedLog can host multiple studies simultaneously. Each study has its own set of users and permissions (see [Permissions](../PERMISSIONS.md)).

### Event

An **Event** represents a timepoint or visit within a study — for example `Baseline`, `Visit-1`, `Month-6`. Events are ordered and define the structure of data collection over time.

### Proband

A **Proband** is a study participant. Probands are identified by a freeform string ID (case-insensitive by default, configurable via `PROBAND_IDS_CASE_SENSETIVE`). MedLog does not store any personal information about the proband beyond this ID — the ID is expected to be a pseudonym.

### Interview

An **Interview** is one data-collection session: a specific proband at a specific event. An interviewer opens an interview, records all current medications, then closes it. Interviews track start/end time and whether the proband has taken any medications at all.

### Intake

An **Intake** is a single medication entry within an interview. It records:

- The drug (looked up from the drug database)
- Daily dose and dosing interval
- Start and end date of the medication period

Custom / off-label drugs that are not in the drug database can be entered as free-text entries.

---

## Workflow

1. An **admin** or **user manager** creates a study and assigns users to it.
2. An **interviewer** selects a study and opens a new interview for a proband at a given event.
3. The interviewer can copy medication entries from the proband's last interview to save time.
4. The interviewer searches the drug database and adds intake entries one by one.
5. The interviewer closes the interview.
6. An **admin** or **study viewer** can export the collected data (see [Export](#export)).

---

## Authentication

MedLog supports two login methods that can be used in parallel:

- **Local accounts** — username + password stored in the MedLog database. Always available unless disabled via `AUTH_BASIC_LOGIN_IS_ENABLED=false`.
- **OIDC providers** — one or more OpenID Connect providers (Keycloak, Authentik, Azure AD, …). Configured via `AUTH_OIDC_PROVIDERS`. Role and study permissions can be derived automatically from OIDC group membership on every login.

For OIDC details see [Configuration](configuration.md#oidc).

---

## Users, Roles & Permissions

MedLog has a two-layer permission model:

- **Global roles** — `medlog-admin` and `medlog-user-manager`, controlling system-wide capabilities.
- **Study permissions** — per-user, per-study flags: `is_study_viewer`, `is_study_interviewer`, `is_study_admin`.

Full documentation: [PERMISSIONS.md](../PERMISSIONS.md)

---

## Drug Database

MedLog requires a drug database to power the medication search. The database is pluggable via the `DRUG_IMPORTER_PLUGIN` setting.

Full documentation: [Drug Database](drug-database.md)

---

## Export

Study data (interviews and intakes) can be exported as CSV. Exports are triggered through the web interface by users with at least viewer access. The export job runs in the background worker and the result file is cached in `EXPORT_CACHE_DIR`.

---

## Background Worker

A background worker process runs alongside the web server and handles:

- Importing / updating the drug database
- Running export jobs
- Cleaning up expired API tokens and old job records

By default the worker runs in a second OS process spawned automatically. For containerised deployments with multiple replicas it can be separated: set `BACKGROUND_WORKER_START_IN_EXTRA_PROCESS=false` on the web server instances and run a dedicated worker container with `python main.py --run_worker_only`.

---

## API

The backend exposes a fully documented REST API. When the server is running, the interactive API docs are available at:

```
http://<host>:<port>/docs
```
