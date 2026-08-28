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

A study can be **cloned** (`POST /api/study/{study_id}/clone`, admins only): the clone gets its own name but reuses the setup of the source study, meaning its proband-ID configuration (pattern, error text, normalization, example) and a copy of its complete event structure. Collected data (interviews, intakes) and study permissions are never copied, so a clone starts empty like a freshly created study.

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

#### Plausibility rules

Beyond checking which fields are present and which are mutually exclusive, the backend
rejects combinations of values that cannot be true. A violation returns **422** with a
`detail` object naming the `rule` that broke and the `fields` it concerns, so the client
can show a hint on the right input.

All date checks compare against the server's current UTC date. Timestamps are stored as
naive UTC while interviewers work in local time, so every comparison gets one day of
tolerance in both directions: a date one day off "today" is never rejected.

| Rule | Rejected because |
| --- | --- |
| `end_date_before_start_date` | `intake_end_date` is before `intake_start_date`. Both on the same day is a valid one-day intake. |
| `start_date_in_future` | The intake has not begun yet, so it cannot be recorded. |
| `end_date_in_future` | The intake cannot have ended yet. |
| `consumed_today_with_past_end_date` | `consumed_meds_today` is `Yes` although the intake already ended. |
| `consumed_today_with_future_start_date` | `consumed_meds_today` is `Yes` although the intake has not begun. |
| `dose_per_day_not_positive` | `dose_per_day` is not greater than 0. |
| `as_needed_dose_unit_not_positive` | `as_needed_dose_unit` is not greater than 0. |
| `start_date_implausibly_old`, `end_date_implausibly_old` | The date is before 1900-01-01, which catches typos such as year `0202`. |

These combinations are explicitly **allowed**:

- `consumed_meds_today` of `No` or `UNKNOWN` with any date combination. Not having taken
  the medication today does not contradict an ongoing intake.
- `intake_end_date_option = ONGOING` with any `consumed_meds_today` answer.
- `intake_start_date_option` / `intake_end_date_option` set instead of an exact date. The
  option carries no date, so the rules that need one are skipped.
- Start and end date on the same day.

The rules are collected in `MedLog/backend/medlogserver/model/intake_rules.py` and are
enforced in `IntakeCRUD`, which every write goes through. On **PATCH** they are evaluated
against the *merged* record (stored row plus payload), so a partial update that only sends
`intake_end_date` is still checked against the stored start date. A PATCH only triggers the
rules that concern a field it actually sends: because the reference date is "now", a record
that was correct when it was entered can become contradictory purely through the passage of
time, and correcting an unrelated field weeks later must not be blocked by that.

Existing rows are **not** migrated. The rules apply to new writes only, so contradictory
records created before this validation existed stay as they are.

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

> [!IMPORTANT]
> **MedLog requires an external OIDC/OAuth2 provider for production use.**
> A built-in local user system exists, but it is intentionally incomplete: there is no self-registration UI and no plans to add one. Local accounts are intended for development and initial admin bootstrapping only — not as a standalone auth solution.
>
> If you have a strong need for full local-user management without an external identity provider, [open an issue](https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues) and let us know.

MedLog supports two login methods:

- **OIDC providers** *(required for production)* — one or more OpenID Connect providers (Keycloak, Authentik, Azure AD, …). Configured via `AUTH_OIDC_PROVIDERS`. Roles and study permissions are derived automatically from OIDC group membership on every login.
- **Local accounts** *(development / bootstrapping only)* — username + password stored in the MedLog database. No self-registration. Accounts can only be created manually by an admin. Can be disabled entirely via `AUTH_BASIC_LOGIN_IS_ENABLED=false` once an OIDC provider is configured.

For OIDC setup details see [Configuration](configuration.md#oidc).

---

## Users, Roles & Permissions

MedLog has a two-layer permission model:

- **Global roles** — `medlog-admin` and `medlog-user-manager`, controlling system-wide capabilities.
- **Study permissions** — per-user, per-study flags: `is_study_viewer`, `is_study_interviewer`, `is_study_admin`.

Full documentation: [PERMISSIONS.md](docs/PERMISSIONS.md)

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
