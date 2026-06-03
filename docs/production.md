# Running MedLog in Production

> [!IMPORTANT]
> These instructions assume you are running on **Linux**. On other operating systems some commands may need to be adapted.

---

## Before You Start

### Drug Database

MedLog requires a drug database. The built-in **dummy dataset** is sufficient for evaluation but contains only a handful of made-up entries. For real clinical use you need a licensed database such as the MMI Pharmindex (GKV Arzneimittelindex).

See [Drug Database](drug-database.md) for details.

### Database

For production use **PostgreSQL**. SQLite is only supported for development and testing.

### Configuration

All settings are supplied via environment variables. See [Configuration](configuration.md) for the full reference. At minimum you must set:

| Variable | Description |
|---|---|
| `SERVER_SESSION_SECRET` | Random string ≥ 64 characters. Generate once, keep secret. |
| `ADMIN_USER_PW` | Password for the built-in admin account. |
| `SQL_DATABASE_URL` | PostgreSQL connection string. |
| `SERVER_HOSTNAME` | The external hostname where MedLog is reachable. |

---

## Option A: Prebuild Container from Docker Hub

This is the recommended way to run MedLog. No build step is required.

**Requirements:** Docker

### Pull the image

```bash
docker pull dzdde/dzdmedlog
```

Tag strategy:

| Tag | Description |
|---|---|
| `latest` | Most recent stable release (built from `main`). |
| `dev` | Most recent development build (built from `dev` on every commit). |
| `1.x.x` | Specific release version. |

### Run with demo mode (evaluation only)

```bash
docker run \
  -v ./database:/data/db \
  -p 8888:8888 \
  -e DEMO_MODE=true \
  dzdde/dzdmedlog
```

Then open http://localhost:8888 and log in as `admin` / `adminadmin`.

> [!WARNING]
> Demo mode uses a random session secret on every restart. All sessions are invalidated when the container restarts. **Do not use demo mode in production.**

### Run with a real configuration

Create a `.env` file with your production settings (see [Configuration](configuration.md)), then:

```bash
docker run \
  -v ./database:/data/db \
  -v ./export:/data/export \
  --env-file .env \
  -p 8888:8888 \
  dzdde/dzdmedlog
```

The container exposes:

| Path | Description |
|---|---|
| `/data/db` | SQLite database file (if using SQLite). Mount a volume here. |
| `/data/export` | Export cache. Mount a volume here. |
| `/data/provisioning` | Optional: drop YAML provisioning files here. |

For PostgreSQL, set `SQL_DATABASE_URL` to your PostgreSQL connection string and omit the `/data/db` volume.

### Separate background worker (optional)

For high-availability setups you can run the web server and the background worker in separate containers:

```bash
# Web server — no background worker
docker run \
  --env-file .env \
  -e BACKGROUND_WORKER_START_IN_EXTRA_PROCESS=false \
  -p 8888:8888 \
  dzdde/dzdmedlog

# Background worker only
docker run \
  --env-file .env \
  dzdde/dzdmedlog --run_worker_only
```

---

## Option B: Build a Local Container Image

**Requirements:** Docker (runnable without `sudo`)

Build the image:

```bash
make container
# or directly:
./build_docker.sh
```

This produces the image tagged `dzdmedlog:latest`. Run it the same way as Option A, replacing `dzdde/dzdmedlog` with `dzdmedlog`:

```bash
docker run \
  -v ./database:/data/db \
  -p 8888:8888 \
  -e DEMO_MODE=true \
  dzdmedlog
```

> [!NOTE]
> If you need to run Docker with `sudo`, edit `build_docker.sh` and prefix the `docker` command accordingly.

---

## Option C: Run from Local Source (no Docker)

**Requirements:**
- Python 3.11+
- bun or npm

Install Python dependencies:

```bash
pip install -U -r MedLog/backend/requirements.txt
```

Build the frontend (static files served by the backend):

```bash
# with bun
cd MedLog/frontend && bun install && bunx nuxi generate

# with npm
cd MedLog/frontend && npm install && npx nuxi generate
```

Set required environment variables and start the server:

```bash
export DEMO_MODE=true   # or set individual production vars
python MedLog/backend/medlogserver/main.py
```

Visit http://localhost:8888

---

## Reverse Proxy & HTTPS

MedLog should be placed behind a reverse proxy (nginx, Caddy, Traefik, …) that handles TLS termination. When doing so:

- Set `SERVER_PROTOCOL=https`
- Set `SERVER_HOSTNAME` to your public domain name
- Set `SET_SESSION_COOKIE_SECURE=true` (this is the default)

---

## Database Migrations

MedLog runs database migrations automatically on startup via Alembic. No manual migration step is needed under normal circumstances.

To run migrations without starting the full server (useful in CI/CD pipelines):

```bash
python MedLog/backend/medlogserver/main.py --setup_database_only
# or use the helper script:
./run_seed_or_update_database.sh
```

---

## First Login

After the first start, log in with:

- **Username:** value of `ADMIN_USER_NAME` (default: `admin`)
- **Password:** value of `ADMIN_USER_PW`

From the admin panel you can create studies, manage users, and configure OIDC providers.
