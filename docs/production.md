# Running MedLog in Production

> [!IMPORTANT]
> These instructions assume you are running on **Linux**. On other operating systems some commands may need to be adapted.

---

## Before You Start

### Drug Database

MedLog requires a drug database. The built-in **dummy dataset** is sufficient for evaluation but contains only a handful of made-up entries. For real clinical use you need a licensed database such as the MMI Pharmindex (GKV Arzneimittelindex).

See [Drug Database](drug-database.md) for details.

### Authentication / OIDC

> [!IMPORTANT]
> MedLog requires an external **OIDC/OAuth2 identity provider** for production use (Keycloak, Authentik, Azure AD, …).
>
> A built-in local user system exists but is intentionally limited: there is no self-registration UI and no plans to add one. Local accounts are only meant for the initial admin setup and development. Do not rely on them as the sole authentication method in a production deployment.
>
> If full local-user management without an external IdP is important to you, [open an issue](https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues).

See [Configuration → OIDC](configuration.md#oidc) for how to wire up your identity provider.

### Database

For production use **PostgreSQL**. SQLite is only supported for development and testing.

### Configuration

All settings are supplied via environment variables. See [Configuration](configuration.md) for the full reference. At minimum you must set:

| Variable | Description |
|---|---|
| `SERVER_SESSION_SECRET` | Random string ≥ 64 characters. Generate once, keep secret. |
| `ADMIN_USER_PW` | Password for the built-in admin account. |
| `SQL_DATABASE_URL` | PostgreSQL connection string. |
| `PUBLIC_URL` | The external URL where MedLog is reachable, e.g. `https://medlog.example.com`. |

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
- npm

Install Python dependencies:

```bash
pip install -U -r MedLog/backend/requirements.txt
```

Build the frontend (static files served by the backend):

```bash
cd MedLog/frontend && npm install && npm run generate
```

Set required environment variables and start the server:

```bash
export DEMO_MODE=true   # or set individual production vars
python MedLog/backend/medlogserver/main.py
```

Visit http://localhost:8888

---

## Reverse Proxy & HTTPS

MedLog should be placed behind a reverse proxy (nginx, Caddy, Traefik, …) that
handles TLS termination. All you need to tell the app is its public address:

```yaml
PUBLIC_URL: "https://medlog.example.com"
SET_SESSION_COOKIE_SECURE: true   # the default
```

### `PUBLIC_URL` is the single source of truth

The proxy terminates TLS and then speaks plain HTTP to the container, so the app
only ever sees an `http://` request arriving on an internal address. Left to its
own devices it would build every absolute URL with `http://` and an internal
hostname, including the OIDC `redirect_uri`. That forces your identity provider
to whitelist a plaintext callback, and the authorization code travels one hop on
a cleartext request line before the proxy upgrades it.

`PUBLIC_URL` states the external address directly and is authoritative for every
generated absolute URL: the OIDC redirect URI, the post-logout redirect URI, and
the login endpoints handed to the web client.

It is **independent of where the server binds**. `SERVER_LISTENING_HOST` and
`SERVER_LISTENING_PORT` only say where the socket is opened, so a container can
bind port 8888 while being served to the world on 443:

```yaml
PUBLIC_URL: "https://medlog.example.com"   # what users type
SERVER_LISTENING_PORT: 8888                # what the container binds
```

Include a port in `PUBLIC_URL` only when users really have to type one
(`https://medlog.example.com:8443`). A path component is not supported: MedLog
cannot be served under a sub-path.

### Migrating from `SERVER_PROTOCOL` / `SERVER_HOSTNAME`

> [!NOTE]
> `SERVER_PROTOCOL` and `SERVER_HOSTNAME` are **deprecated but still fully
> supported**. Existing deployments keep working unchanged; the app logs a
> warning at startup naming the exact `PUBLIC_URL` to replace them with.

The old settings built the public URL from three values, one of which had an
unrelated job:

```
SERVER_PROTOCOL + SERVER_HOSTNAME + SERVER_LISTENING_PORT
```

Because the *listening* port was spliced into the *public* URL, and only 80 and
443 suppressed the `:port` suffix, a deployment behind a TLS proxy had to set
`SERVER_LISTENING_PORT=443` just to stop `https://example.org:8888` from being
generated. The container then served plaintext HTTP on port 443, which is why
its healthcheck reads `wget http://localhost:443` and looks broken at a glance.

Replace all three with one line:

```diff
- SERVER_PROTOCOL: "https"
- SERVER_HOSTNAME: "medlog.example.com"
- SERVER_LISTENING_PORT: 443
+ PUBLIC_URL: "https://medlog.example.com"
```

If both styles are set, `PUBLIC_URL` wins.

### Trusting forwarded headers (optional)

`PUBLIC_URL` fixes the scheme and hostname on its own, without trusting anything
the proxy sends. Listing your proxy in `SERVER_TRUSTED_PROXIES` additionally
records the **real client IP** on user sessions instead of the proxy's:

```yaml
SERVER_TRUSTED_PROXIES: '["10.33.0.200"]'   # or a network: ["10.33.0.0/24"]
```

This is the address the proxy connects *from*, which in Docker is its address on
the shared network, **not** `127.0.0.1`. The default is `["127.0.0.1", "::1"]`,
which covers a proxy running directly on the host.

`X-Forwarded-*` headers can be forged by any client, so they are honoured only
for peers on this list. Never set it to `*` in production: that lets any client
dictate the host and scheme of generated URLs.

An explicit `PUBLIC_URL` outranks `X-Forwarded-Proto` and `X-Forwarded-Host`, so
the generated URLs are the same no matter which hostname a request arrived on.
To serve the app under several hostnames and have each request keep its own,
leave `PUBLIC_URL` unset and let the trusted proxy supply the host per request.

### What the proxy has to send

**Traefik v3** sets `X-Forwarded-Proto`, `X-Forwarded-Host` and `X-Forwarded-For`
automatically. No extra configuration is needed beyond routing to the TLS
entrypoint:

```yaml
labels:
  - traefik.enable=true
  - traefik.http.services.srv-medlog.loadbalancer.server.port=8888
  - traefik.http.routers.rt-medlog.rule=Host(`medlog.example.com`)
  - traefik.http.routers.rt-medlog.entrypoints=webtls
  - traefik.http.routers.rt-medlog.tls=true
```

**nginx** must be told explicitly:

```nginx
location / {
    proxy_pass         http://medlog:8888;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Forwarded-Proto $scheme;
    proxy_set_header   X-Forwarded-Host  $host;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
}
```

### Local development

Plain HTTP development is unaffected. With nothing configured the public URL
falls back to `http://localhost:<listening port>`, so nothing is ever silently
upgraded to `https` and `http://localhost:8888` keeps working as before.

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
