# API Tokens

API tokens let scripts and other programs use the MedLog REST API without a browser session, for example a nightly export job. A token is sent as a bearer token:

```bash
curl -H "Authorization: Bearer <token>" https://medlog.example.com/api/user/me
```

A token acts with the full permissions of the user it belongs to (global roles and study permissions, see [PERMISSIONS.md](PERMISSIONS.md)). There are no scopes or read-only tokens. Treat a token like a password.

---

## Two kinds of tokens

MedLog issues tokens in two ways. Both are used the same way, but they live differently.

| | Login tokens | Managed tokens |
|---|---|---|
| Created via | `POST /api/auth/basic/login/token` or `/api/auth/oidc/login/{provider_slug}/token` | `POST /api/user/me/api-token` (token management) |
| Bound to | The login they were created with | The user |
| Lifetime | `API_TOKEN_DEFAULT_EXPIRY_TIME_MINUTES` (basic login) or the OIDC login | Chosen by the user within the configured limits |
| Survives logout of the browser session | No, ends with its login | Yes |
| Has a name | No | Yes |
| Needs `API_TOKEN_MANAGEMENT_ENABLED` | No | Yes |

Login tokens are meant for short-lived use. Managed tokens are the right choice for anything that runs unattended over weeks or months.

---

## Enabling the token management

Managed tokens are off by default. To enable them set:

```bash
API_TOKEN_MANAGEMENT_ENABLED=true
```

The related settings, all optional:

| Variable | Default | Meaning |
|---|---|---|
| `API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS` | `30` | Lifetime if the user does not choose one. |
| `API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS` | `365` | Longest lifetime a user may choose. `None` allows tokens without expiry. |
| `API_TOKEN_MANAGEMENT_MAX_TOKENS_PER_USER` | `20` | Maximum number of unexpired managed tokens per user. `None` for no limit. |
| `API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS` | `30` | Pauses the tokens of OIDC users whose last login is older than this. See [OIDC users](#oidc-users). |

`API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS` must not be larger than `API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS`, otherwise the server refuses to start. A lifetime can never exceed 3650 days, even when `API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS` is `None`.

Full descriptions are in the [Configuration Reference](configuration.md#api_token_management_enabled).

Switching the feature off later does not delete any tokens, but all managed tokens are rejected until it is switched on again. Login tokens are not affected by this setting.

---

## Managing your own tokens

The endpoints below only accept a **browser session login**. A request authenticated with an API token gets `403`. This prevents a leaked token from creating new tokens that would outlive its own expiry or revocation.

While logged in to MedLog in the browser, the endpoints can be tried out directly in the interactive API docs at `/docs`, which send the session cookie along.

| Method and path | What it does |
|---|---|
| `GET /api/config/api-token` | Returns the token management settings (enabled, lifetime limits, token limit). Needs no login. The web client uses it to render the token management. |
| `GET /api/user/me/api-token` | Lists all your tokens, newest first, including your login tokens. |
| `POST /api/user/me/api-token` | Creates a managed token. |
| `DELETE /api/user/me/api-token/{id}` | Revokes one of your tokens. It stops working immediately. |

If the feature is disabled, all `/api/user/me/api-token` endpoints answer with `403`.

### Creating a token

```json
POST /api/user/me/api-token
{
  "name": "Nightly export script",
  "expires_in_days": 90
}
```

- `name` is required (1 to 128 characters) and only helps you recognise the token later.
- Omit `expires_in_days` to get `API_TOKEN_MANAGEMENT_DEFAULT_EXPIRY_DAYS`.
- An explicit `"expires_in_days": null` creates a token that never expires. This is only accepted if `API_TOKEN_MANAGEMENT_MAX_EXPIRY_DAYS` is `None`.
- A lifetime above the maximum answers `422`. Reaching `API_TOKEN_MANAGEMENT_MAX_TOKENS_PER_USER` answers `409`, revoke a token you no longer need first.

The response (`201`) contains the complete token in the `token` field. **It is shown only this once.** MedLog stores only a hash and cannot show the token again. If it gets lost, revoke it and create a new one.

### What the token list shows

| Field | Meaning |
|---|---|
| `id` | Used to revoke the token. |
| `name` | The name given on creation, `null` for login tokens. |
| `token_prefix` | The public part of the token, everything before the dot. Compare it with the start of a token you have in use to find the matching entry. |
| `created_via` | `token_management` for managed tokens, `login` for login tokens. |
| `created_at`, `expires_at` | Creation and expiry time in UTC. `expires_at` is `null` for tokens without expiry. |
| `last_used_at` | Last successful use in UTC, accurate to about a minute. `null` if never used. |
| `expired` | `true` once `expires_at` has passed. Expired tokens are removed by the background worker after a while. |

---

## Revoking tokens of other users

User managers and admins can list and revoke the tokens of any user, for example when a token leaked or a person leaves the project:

| Method and path | What it does |
|---|---|
| `GET /api/user/{user_id}/api-token` | Lists the tokens of a user, also of deactivated users. |
| `DELETE /api/user/{user_id}/api-token/{id}` | Revokes one token of the user. |

These endpoints work regardless of `API_TOKEN_MANAGEMENT_ENABLED`, so leftover tokens can still be cleaned up after the feature was switched off.

---

## When a managed token stops working

A managed token is rejected with `401` when any of these apply:

- it expired,
- it was revoked by the user or a user manager,
- the user was deactivated,
- `API_TOKEN_MANAGEMENT_ENABLED` is off,
- the user logs in via OIDC and the last OIDC login is too old (see below).

Logging out of the browser session does **not** affect managed tokens. A token itself can be revoked by sending it to `POST /api/auth/logout` as bearer token.

### OIDC users

MedLog only syncs roles and study permissions of OIDC users from the identity provider at login, and it does not learn when a user is removed from the provider. Without a limit, a managed token would keep the access the user had at their last login until the token expires, even if the user lost that access in the provider long ago.

Therefore managed tokens of a user who has ever logged in via OIDC **pause** when that last OIDC login is older than `API_TOKEN_MANAGEMENT_OIDC_LOGIN_MAX_AGE_DAYS`. The API then answers `401` with a message asking the user to log in again. After the next login in the browser the tokens work again, with the freshly synced permissions.

Tell users who run long-lived scripts to log in to MedLog at least once within that period. Set the variable to `None` to disable the pause. Users without any OIDC login, such as local accounts, are not affected.

---

## Notes for operators

- **Storage:** tokens are stored as SHA-256 hashes. Tokens created before this change were hashed with PBKDF2. They keep working and are rehashed automatically on their next successful use. No manual step is needed.
- **Database:** the feature adds columns to the user and user auth tables. The migration runs automatically on startup (see [Database Migrations](production.md#database-migrations)).
- **Cleanup:** the background worker deletes expired login and managed tokens. Managed tokens are never deleted because of a logout or an expired OIDC login.
- **Last use:** `last_used_at` is written at most once per minute per token, so a busy script does not cause a database write on every request.
