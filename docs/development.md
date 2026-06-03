# Development Guide

> [!IMPORTANT]
> These instructions assume you are developing on **Linux**. On other operating systems some steps may need to be adapted.

---

## Prerequisites

- Git
- Python 3.11 or higher (the setup script manages the exact version via `uv`)
- Docker (for PostgreSQL dev containers and running tests against Postgres)
- [bun](https://bun.sh) or npm/node (the setup script installs bun automatically)

---

## 1. Clone and Branch

```bash
git clone https://github.com/DZD-eV-Diabetes-Research/DZDMedLog.git
cd DZDMedLog
git checkout dev
```

Create a feature branch if you are contributing:

```bash
git checkout -b feature/issue-123-short-description
```

See [Branch Strategy](#branch-strategy) for naming conventions.

---

## 2. Set Up the Backend (Python)

The setup script installs [`uv`](https://docs.astral.sh/uv/) (a fast Python version/package manager) and creates a virtual environment at `.medlog-python-env/`.

> [!IMPORTANT]
> This script must be **sourced**, not executed. Sourcing activates the virtual environment in your current shell.

```bash
source build_server_dev_env.sh
```

What it does:
- Installs `uv` if not present
- Creates a virtual environment with the correct Python version
- Installs all backend dependencies from `MedLog/backend/requirements.txt` and `requirements_tests.txt`
- Activates the environment

If you prefer to manage the environment yourself:

```bash
pip install -r MedLog/backend/requirements.txt
pip install -r MedLog/backend/requirements_tests.txt
```

---

## 3. Set Up the Frontend (TypeScript / Nuxt)

```bash
./build_client_dev_env.sh
```

This installs bun (or updates it if present) and runs `bun install` in `MedLog/frontend/`.

If you prefer a different package manager:

```bash
cd MedLog/frontend
npm install   # or: yarn install / pnpm install
```

---

## 4. Start the Backend

Choose one of the run scripts depending on what you need:

### Standard: SQLite + OIDC mock

The simplest option. Uses SQLite as the database and an in-process OIDC mock server so you can log in without any external dependency.

```bash
./run_dev_backend_server_with_oidc.sh
```

The script starts:
- An OIDC mock server on port **8884**
- The MedLog backend server on port **8888**
- The background worker as a separate process

### With PostgreSQL + OIDC mock

```bash
./run_dev_backend_server_with_oidc_on_postgres.sh
```

Manages a `medlog-dev-postgres` Docker container on port **5433** automatically. Pass `--reset` to wipe and recreate the database:

```bash
./run_dev_backend_server_with_oidc_on_postgres.sh --reset
```

### With FTP drug data mock + OIDC mock

Tests the MMI Pharmindex FTP auto-update pipeline locally:

```bash
./run_dev_backend_server_with_oidc_and_drug_ftp.sh
```

### Manual start (no scripts)

If you need more control:

```bash
export LOG_LEVEL=DEBUG
export SERVER_SESSION_SECRET=IAMASTUPIDDUMMYANDTHATSOKSDEALWITHITINEEDTOBE64CHARSLONGTHATWHYIKEEPTALKING
export ADMIN_USER_PW=password123
export SERVER_HOSTNAME=localhost
export DEMO_MODE=true

python MedLog/backend/medlogserver/main.py
```

---

## 5. Start the Frontend Dev Server

In a second terminal (with the backend already running):

```bash
cd MedLog/frontend
bun run dev
```

The Nuxt dev server starts on **http://localhost:3000** with hot-reload.

The backend API is proxied automatically. The interactive API docs are at **http://localhost:8888/docs**.

---

## 6. Dev Login: Test Users

When using any of the `run_dev_backend_server_with_oidc*.sh` scripts, a mock OIDC server provides these preconfigured users. On the login screen, click **LocalDevLogin**, then pick a user:

| Username | OIDC groups | MedLog role / permissions |
|---|---|---|
| `admin` | `medlog-admins` | Full admin |
| `admin2` | `medlog-admins` | Full admin |
| `user1` | `interviewer-study1` | Interviewer for `study1` |
| `user2` | _(none)_ | Plain user (no study access by default) |
| `user3` | _(none)_ | Plain user |

The local admin account (username `admin`, password `password123`) is also available via basic login.

---

## 7. Reset the Dev Database

Stop the backend, delete the SQLite file, and restart:

```bash
rm local.sqlite local.sqlite-shm local.sqlite-wal 2>/dev/null; true
./run_dev_backend_server_with_oidc.sh
```

For PostgreSQL, use the `--reset` flag (see above).

---

## 8. Testing

### Backend tests with SQLite

```bash
./run_backend_tests_with_sqlite.sh
```

Pass `--dev` to stop on the first failure and show full tracebacks:

```bash
./run_backend_tests_with_sqlite.sh --dev
```

### Backend tests with PostgreSQL

Requires Docker. Starts a Postgres container automatically:

```bash
./run_backend_tests_with_postgres.sh
./run_backend_tests_with_postgres.sh --dev
```

### Run pytest directly

After activating the dev env, you can pass any pytest flags directly:

```bash
python -m pytest MedLog/backend/tests --db=sqlite -k test_drug
```

---

## 9. Building

### Build the frontend static files

Generates the static Nuxt output in `MedLog/frontend/.output/public/` which the Python backend serves:

```bash
make frontend
# or:
./build_static_client.sh
```

Uses a Docker container with bun — no local bun installation needed.

### Build the Docker image

```bash
make container
# or:
./build_docker.sh [optional-tag]
```

Produces image `dzdmedlog:latest` (or the tag you provide).

---

## 10. Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-grade code. Source for releases. |
| `dev` | Latest running version. A container image is built automatically on every commit. |
| `feature/issue-NNN-*` | New features. |
| `fix/issue-NNN-*` | Bug fixes. |
| `refactor/issue-NNN-*` | Refactoring. |
| `experiment/issue-NNN-*` | Experimental work. |

Start branch names with the related issue number: `fix/issue-129-worker-crash`.

When a sub-branch is ready, merge it into `dev` to build a new image for testing. Merges into `main` are done when a new release is created.

---

## 11. Database Migration Scripts

When you change a SQLModel model, create an Alembic migration:

```bash
./run_database_migration_scripts_creation.sh
```

Review the generated migration in `MedLog/backend/medlogserver/db_migrations/versions/` before committing.

---

## 12. Requirement Files

Dependencies are declared in `MedLog/backend/pyproject.toml` and compiled to pinned requirement files. To regenerate them:

```bash
./build_requirement_files.sh
```

This produces:
- `MedLog/backend/requirements.txt` — runtime dependencies
- `MedLog/backend/requirements_tests.txt` — runtime + test dependencies
- `MedLog/backend/requirements_docs.txt` — runtime + docs dependencies
