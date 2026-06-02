# MedLog: Users, Roles and Study Permissions

MedLog has two independent permission layers that work together:

1. **Global roles** control what a user can do across the entire system.
2. **Study permissions** control what a user can do within a specific study.

---

## Global Roles

A user can hold zero or more of the following roles.

| Role | Config name | What the role allows |
|---|---|---|
| Admin | `medlog-admin` | Full access to everything. Implicit full access to all studies without needing an explicit study permission. Can manage users, studies, and all data. |
| User manager | `medlog-user-manager` | Can create and deactivate user accounts and manage study permissions for any user. Can view (but not interview into) all studies. Cannot grant the admin role. |

A user with no global role is a plain user. They can only access studies where they hold an explicit study permission.

Global roles can be assigned:
- Manually by an admin in the user management interface.
- Automatically on every OIDC login via `ROLE_MAPPING` (see below).

---

## Study Permissions

Study permissions are granted per user per study. A single record holds three independent flags.

| Flag | Default | What it allows |
|---|---|---|
| `is_study_viewer` | on | Read access to all data in the study. |
| `is_study_interviewer` | off | Everything a viewer can do, plus creating and editing interview entries. |
| `is_study_admin` | off | Everything a viewer can do, plus managing which users have access to this study. Does **not** grant system-wide user management. |

Flags are independent, so a user can for example be both an interviewer and a study admin without being a system-level user manager.

Study permissions can be set:
- Manually by a user manager or a study admin via the permissions interface.
- Automatically on every OIDC login via `STUDY_PERMISSION_MAPPING` (see below).

---

## What each role can do: quick reference

| Action | Plain user | Study admin | User manager | Admin |
|---|:---:|:---:|:---:|:---:|
| View study data | own studies only | own studies only | all studies | all studies |
| Create interviews | if `is_study_interviewer` | if `is_study_interviewer` | no | yes |
| Manage study memberships | no | own study | all studies | all studies |
| Create / deactivate users | no | no | yes | yes |
| Assign global roles | no | no | no | yes |
| Access all studies without explicit permission | no | no | view only | yes |

---

## OIDC Login Behaviour

When a user logs in via OIDC the following happens on **every** login, not just the first one.

### User profile

The fields below are always updated from the current OIDC claims.

| Field | Source claim |
|---|---|
| Display name | configured via `USER_DISPLAY_NAME_ATTRIBUTE` (default: `display_name`) |
| E-mail address | configured via `USER_MAIL_ATTRIBUTE` (default: `email`) |
| E-mail verified | standard `email_verified` claim |

### Global roles (`ROLE_MAPPING`)

The user's global roles are **fully replaced** with whatever the current OIDC group membership maps to. If a user was removed from every mapped group, all their OIDC-derived roles are removed on the next login.

Configuration example:

```json
"ROLE_MAPPING": {
  "idp-group-admins":       ["medlog-admin"],
  "idp-group-user-managers":["medlog-user-manager"]
}
```

Groups listed in `ROLE_MAPPING` are also matched directly against the role names `medlog-admin` / `medlog-user-manager` without needing an explicit mapping entry.

### Study permissions (`STUDY_PERMISSION_MAPPING`)

OIDC can grant and revoke specific permission flags on specific studies based on group membership.

Configuration example:

```json
"STUDY_PERMISSION_MAPPING": {
  "MyStudy": {
    "idp-group-interviewers": ["is_study_interviewer"],
    "idp-group-exporters":    ["is_study_viewer"],
    "idp-group-study-admins": ["is_study_admin"]
  }
}
```

Each key under the study name is an OIDC group. Its value is a list of permission flags to grant when the user is a member.

**OIDC only touches the flags it is configured to manage.** If the mapping for a study only mentions `is_study_interviewer`, the `is_study_admin` and `is_study_viewer` flags are never read or changed by OIDC, regardless of group membership.

---

## Manual permissions and OIDC: who wins?

A user manager can always grant permissions manually in addition to or instead of what OIDC provides. The two sources coexist as follows.

| Situation | Result |
|---|---|
| OIDC grants a flag, user manager also sets a **different** flag | Both are kept. OIDC revocation only affects the flag OIDC manages. |
| OIDC grants a flag, user manager explicitly sets the **same** flag | User manager takes ownership. OIDC will no longer revoke that flag, even if the user leaves the group. |
| OIDC revokes a flag, user manager had never touched it | Flag is revoked. |
| All OIDC-granted flags for a study are revoked and no manual flags remain | The permission record is deleted entirely. |

In short: once a user manager explicitly sets a flag, that flag belongs to the user manager and is immune to OIDC revocation. To remove it, the user manager (or an admin) must revoke it manually.

---

## First login and account creation

If `AUTO_CREATE_AUTHORIZED_USER` is enabled (the default), a MedLog account is created automatically on first OIDC login. The account inherits the display name, e-mail, and permissions derived from group membership at that moment.

If `PREFIX_USERNAME_WITH_PROVIDER_SLUG` is enabled, the username is prefixed with the OIDC provider's slug (e.g. `myidp_john.doe`) to avoid conflicts when multiple OIDC providers are configured.

If `AUTO_CREATE_AUTHORIZED_USER` is disabled, only users who already have a local account can log in via OIDC.

---

## Summary: permission sources

| Source | Global roles | Study permissions |
|---|---|---|
| Manual (admin) | Can assign any role | Can grant/revoke any flag |
| Manual (user manager) | Cannot assign global roles | Can grant/revoke any flag |
| Manual (study admin) | No | Can grant/revoke flags within own study |
| OIDC `ROLE_MAPPING` | Fully replaces on every login | No |
| OIDC `STUDY_PERMISSION_MAPPING` | No | Synced on every login; respects manual ownership |
