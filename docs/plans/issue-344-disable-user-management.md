# Issue #344: hide permission management in the UI (backend part)

Issue: https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/344

> Note: the plan file was requested as `issue-334-...`. The issue is #344, so the file is
> named after the real issue number.

## Problem

When roles and study permissions come from OIDC group mappings, the in-app permission
management is misleading: every change is overwritten on the user's next login. Non-technical
user managers cannot tell which place is the authoritative one.

The backend therefore has to tell the client "do not offer permission management here".

## Decisions taken before planning

Three points were left open in the issue thread. They were decided as follows:

1. **Hint only, no API enforcement.** The backend publishes a flag; it does *not* start
   rejecting role or permission writes. An admin with an API key can still set a permission
   that OIDC overrides on the next login. This is accepted for now (see
   [Follow-ups](#follow-ups-explicitly-out-of-scope)).

   Reasons, beyond "the issue is about the UI":

   * **A hard block would break a feature that already ships.**
     `StudyPermissonCRUD.oidc_set_permissions`
     ([db/study_permission.py:142](../../MedLog/backend/medlogserver/db/study_permission.py#L142),
     issue #305) deliberately lets manually granted flags and OIDC-managed flags coexist:
     OIDC only claims a flag that is currently `False` and only revokes flags it owns.
     Refusing permission writes on an OIDC instance would make that per-flag ownership
     tracking pointless, so hard-disabling is not "the same feature, stricter" - it removes
     one.
   * **It keeps a break-glass path.** Granting a permission via the API for the rest of a
     session (support access, an urgent export) stays possible. There is no other route to
     that once writes are refused.
   * **The audience does not overlap.** The problem in the issue is a *non-technical* user
     manager not knowing which place is authoritative. Someone using an API key is not that
     person.
   * **Asymmetric risk.** Adding enforcement later is additive. Shipping enforcement and
     then discovering an instance needs the escape hatch means a rollback.

   abrain leaned the other way in the issue thread ("it's probably easier to disable changes
   entirely"). Record the decision as a reply on #344 rather than only here.

2. **Explicit config wins, auto-derivation is the default.** `DISABLE_UI_PERMISSION_MANAGEMENT`
   is tri-state: unset means "derive from the OIDC configuration", an explicit `true`/`false`
   always wins. So a normal OIDC install behaves correctly with zero extra configuration,
   and an operator can still force either behaviour.
3. **Per-study signal is part of this change** (abrain's proposal). Each study reports whether
   its permissions are managed via `STUDY_PERMISSION_MAPPING`, which also gives the client
   what it needs to warn when an OIDC-mapped study is renamed.

## What exists today

* `Config.AUTH_OIDC_PROVIDERS` is a list of `Config.OpenIDConnectProvider`, each with
  `ROLE_MAPPING` (OIDC group to MedLog role) and `STUDY_PERMISSION_MAPPING`
  (study *display name* to OIDC group to permission flags), see
  [config.py:608-645](../../MedLog/backend/medlogserver/config.py#L608).
* [oidc_mappings.py](../../MedLog/backend/medlogserver/api/auth/oidc_mappings.py) re-applies both
  mappings on **every** login and tracks per-flag ownership in
  `StudyPermisson.oidc_managed_permissions`, so manually granted flags survive.
* `STUDY_PERMISSION_MAPPING` is keyed by `Study.display_name` and resolved with an exact match
  (`StudyCRUD.get_by_name`, [db/study.py:69](../../MedLog/backend/medlogserver/db/study.py#L69)).
  Renaming a mapped study silently detaches it from the mapping. That is exactly the case
  abrain wants the client to warn about.
* `BrandingData` currently carries only `support_email`, filled in
  [routes_config.py:69](../../MedLog/backend/medlogserver/api/routes/routes_config.py#L69).
* Study endpoints return the SQLModel table class `Study` directly
  (`GET/POST /study`, `POST /study/{id}/clone`, `PATCH /study/{id}`).

## Change 1: config setting and resolvers

File: `MedLog/backend/medlogserver/config.py`

Add a module level constant next to the other module level definitions:

```python
# The study permission flags that STUDY_PERMISSION_MAPPING may reference.
# Lives here (and not in the model layer) so config-level helpers can validate a
# mapping without importing the model layer, which imports Config itself.
VALID_STUDY_PERMISSION_FLAGS: Tuple[str, ...] = (
    "is_study_viewer",
    "is_study_interviewer",
    "is_study_admin",
)
```

Add the setting directly after `BRANDING_SUPPORT_EMAIL_ADDRESS` (it is delivered through the
same endpoint):

```python
DISABLE_UI_PERMISSION_MANAGEMENT: Optional[bool] = Field(
    default=None,
    description=(
        "Hide the role and permission management controls in the web client. "
        "Useful when roles and study permissions are managed via OIDC group mappings, "
        "where in-app changes are overwritten on the user's next login. "
        "Leave unset (default) to derive the value automatically: it is then true as soon "
        "as any configured OIDC provider has a non-empty ROLE_MAPPING. "
        "Set it explicitly to true or false to override that. "
        "This only affects what the web client offers; the API keeps accepting "
        "role and permission changes."
    ),
    examples=[True],
)
```

Add three helper methods to `Config`, following the existing `get_server_url()` style:

```python
def oidc_role_mapping_is_configured(self) -> bool:
    """True if any OIDC provider maps groups to global MedLog roles."""

def is_ui_permission_management_disabled(self) -> bool:
    """Resolved value of DISABLE_UI_PERMISSION_MANAGEMENT.

    An explicitly configured value always wins; otherwise it is derived from
    oidc_role_mapping_is_configured().
    """

def get_oidc_managed_study_permissions(self, study_display_name: str) -> List[str]:
    """Permission flags OIDC manages for the study with this display name.

    Union across all providers, restricted to VALID_STUDY_PERMISSION_FLAGS, sorted
    for a stable API response. Empty list means the study is not OIDC-managed.
    Matching is exact on the display name, mirroring StudyCRUD.get_by_name.
    """
```

All three tolerate `AUTH_OIDC_PROVIDERS is None`.

File: `MedLog/backend/medlogserver/api/auth/oidc_mappings.py`

Replace the local `_VALID_STUDY_PERMISSIONS` set with the new shared constant so there is one
source of truth for the flag names. Pure refactor, no behaviour change.

## Change 2: branding endpoint

File: `MedLog/backend/medlogserver/model/branding_data.py`

```python
disable_ui_permission_management: bool = Field(
    default=False,
    description=(
        "If true the web client hides its role and permission management controls, "
        "because roles are managed outside of MedLog (OIDC group mapping)."
    ),
)
```

**Field name:** the issue body spells the response field `disable_ui_permission_managament`
in one place and `disable_ui_permission_management` in another. The plan uses the correct
spelling. This has to be communicated to the frontend work, since the frontend has not been
written yet (see [Handover](#handover-to-the-frontend-work)).

File: `MedLog/backend/medlogserver/api/routes/routes_config.py`

```python
return BrandingData(
    support_email=config.BRANDING_SUPPORT_EMAIL_ADDRESS,
    disable_ui_permission_management=config.is_ui_permission_management_disabled(),
)
```

`/config/branding` is unauthenticated today and stays that way. The new field leaks only the
boolean "roles come from somewhere else", not any OIDC configuration detail.

## Change 3: per-study OIDC signal

`Study` is a `table=True` SQLModel, so computed API-only fields cannot be added to it. Add a
read model next to it instead, mirroring the existing `StudyExport` pattern.

File: `MedLog/backend/medlogserver/model/study.py`

```python
class StudyApiRead(StudyCreate, BaseTable, TimestampModel, table=False):
    """Study as returned by the API: the stored study plus config-derived OIDC facts."""

    # `StudyCreate` declares `id` as `Optional[uuid.UUID]`; `Study` re-declares it as
    # required. A read model built on `StudyCreate` inherits the Optional version, so
    # without this override all four study endpoints would start advertising a nullable
    # `id` in the OpenAPI schema. Harmless at runtime, but a visible contract change for
    # any generated client, so keep `id` required.
    id: uuid.UUID

    oidc_managed_permissions: List[str] = Field(
        default_factory=list,
        description=(
            "Study permission flags managed by an OIDC group mapping for this study "
            "(STUDY_PERMISSION_MAPPING). These flags are re-applied on every login of a "
            "mapped user, so changing them in the UI has no lasting effect. Empty when the "
            "study is not referenced by any mapping."
        ),
    )
    is_oidc_permission_managed: bool = Field(
        default=False,
        description=(
            "Convenience flag: true when oidc_managed_permissions is non-empty. Clients "
            "should hide the study's permission management and warn before renaming the "
            "study, because the mapping is keyed by the study's display name."
        ),
    )

    @classmethod
    def from_study(cls, study: "Study") -> "StudyApiRead":
        managed = config.get_oidc_managed_study_permissions(study.display_name)
        return cls.model_validate(
            study,
            update={
                "oidc_managed_permissions": managed,
                "is_oidc_permission_managed": bool(managed),
            },
        )
```

The name `oidc_managed_permissions` deliberately matches the field of the same name on
`StudyPermisson`: same meaning, once per study (what OIDC *may* manage) and once per user
record (what OIDC *does* own).

File: `MedLog/backend/medlogserver/api/routes/routes_study.py`

Switch the response models of the four endpoints that return a study to `StudyApiRead` and wrap
the returned objects with `StudyApiRead.from_study(...)`:

| Endpoint | Today | After |
|---|---|---|
| `GET /study` | `PaginatedResponse[Study]` | `PaginatedResponse[StudyApiRead]` |
| `POST /study` | `Study` | `StudyApiRead` |
| `POST /study/{study_id}/clone` | `Study` | `StudyApiRead` |
| `PATCH /study/{study_id}` | `Study` | `StudyApiRead` |

Notes:

* `create_query_params_class(Study)` (sorting and pagination) keeps using `Study`; the enrichment
  happens after ordering and slicing, so only the page that is actually returned is enriched.
* The derivation is pure config plus the study name, so there is no extra database query and no
  measurable cost in `GET /study`.
* `StudyPermissionRead.study_ref` stays a plain `Study`; nested refs are not enriched. The access
  page gets the study itself from `GET /study`.
* `StudyExport` is untouched, so exports keep their current shape.

## Change 4 (sidequest): a deactivated OIDC user must be refused

Found while planning, small enough to fix here instead of in its own issue. It is also what
makes the `Deaktivieren` decision below defensible: the button stays visible, so it has to work.

[routes_auth.py:369](../../MedLog/backend/medlogserver/api/routes/routes_auth.py#L369) resolves
the OIDC user with

```python
user = await user_crud.get_by_user_name(user_name=userinfo.preferred_username)
```

`get_by_user_name` defaults to `show_deactivated=False`, so a deactivated user comes back as
`None`. With `AUTO_CREATE_AUTHORIZED_USER` enabled the next branch then tries to *create* the
user again and dies on the unique `user_name` constraint; the user sees a 500 instead of a 401,
and deactivating an OIDC user is effectively not possible.

Fix: look the user up including deactivated ones and refuse explicitly, before the auto-create
branch.

```python
user = await user_crud.get_by_user_name(
    user_name=userinfo.preferred_username, show_deactivated=True
)
if user is not None and user.deactivated:
    # Deactivation is a local decision the IdP knows nothing about, so it has to be
    # enforced here. Without show_deactivated=True the lookup returns None and the
    # auto-create branch below would try to recreate the user.
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
if user is None and oauth_config.AUTO_CREATE_AUTHORIZED_USER:
    ...
```

The local login path already behaves correctly and is not touched:
[routes_auth.py:231](../../MedLog/backend/medlogserver/api/routes/routes_auth.py#L231) uses
`get_by_user_name_or_email(..., raise_exception_if_none=login_failed_exception)` with
`include_deactivated` left at `False`, which turns a deactivated user straight into a 401. It has
no auto-create fallback, which is why only the OIDC path is affected.

## Resulting contract for the client

| Client decision | Source |
|---|---|
| Hide `Rollen bearbeiten` on `/manage/users` | `branding.disable_ui_permission_management` |
| Hide `Bearbeiten`, `Widerrufen`, `Rechte vergeben` on a study's access page | `branding.disable_ui_permission_management` **or** that study's `is_oidc_permission_managed` |
| Warn before renaming a study | that study's `is_oidc_permission_managed` |
| Explain *which* flags are futile to change for a study | that study's `oidc_managed_permissions` |

Rationale for the "or": the global flag is derived from `ROLE_MAPPING` (global roles) while the
per-study flag comes from `STUDY_PERMISSION_MAPPING`. They are independent, so each field keeps a
single honest meaning and the client combines them. An operator who sets
`DISABLE_UI_PERMISSION_MANAGEMENT=true` by hand still gets everything hidden.

### `Deaktivieren` is deliberately *not* in that table

The issue body lists the `Deaktivieren` button on `/manage/users`
([UserManagement/Table.vue:95](../../MedLog/frontend/components/UserManagement/Table.vue#L95))
among the controls to hide. It does not belong under this flag.

The flag means "OIDC overwrites this on the next login". Deactivating a user is not
overwritten: nothing in [oidc_mappings.py](../../MedLog/backend/medlogserver/api/auth/oidc_mappings.py)
or in the OIDC login path touches `User.deactivated`. Hiding the button would therefore
remove the only in-app way to lock a user out, for a control OIDC does not contest.

Keeping the button visible does mean it has to actually work, and today it does not for OIDC
users. That is fixed as a sidequest in [Change 4](#change-4-sidequest-a-deactivated-oidc-user-must-be-refused).

So: `Deaktivieren` stays visible. If it should be hidden anyway, that is a separate product
decision with its own reason ("user lifecycle is managed in the IdP"), not this flag.

## Tests

New file `MedLog/backend/tests/tests_permission_management_flags.py`, in the in-process style of
`tests_public_url.py` (build `Config(**overrides)` directly, no live server):

* unset plus no OIDC provider gives `False`
* unset plus a provider with a non-empty `ROLE_MAPPING` gives `True`
* unset plus a provider that has only `STUDY_PERMISSION_MAPPING` gives `False`
  (documents the split contract above)
* explicit `False` beats a configured `ROLE_MAPPING`
* explicit `True` with no OIDC provider at all
* `get_oidc_managed_study_permissions` returns the sorted union across two providers, drops
  unknown flag names, is empty for an unmapped study, and is empty when a study is renamed
  (exact-name match)

Extend `MedLog/backend/tests/tests_config.py`:

* `test_endpoint_config_branding_get` also asserts the new key. The test suite starts the server
  with an OIDC provider whose `ROLE_MAPPING` is non-empty
  ([conftest.py:193](../../MedLog/backend/tests/conftest.py#L193)), so the expected value is
  `True` and the live suite covers the derived path end to end.

Extend `MedLog/backend/tests/tests_study.py`:

* `GET /study` items carry `is_oidc_permission_managed` and `oidc_managed_permissions`
* a study created by the test suite that is not in `STUDY_PERMISSION_MAPPING` reports
  `False` / `[]`
* the OIDC-mapped study (`OIDC_TEST_STUDY_NAME`, auto-created via
  `AUTO_CREATE_STUDY_FROM_MAPPING`) reports `True` and exactly
  `["is_study_admin", "is_study_interviewer"]`. This assertion belongs in
  `tests_oidc_mapping.py` instead, since the study only exists after an OIDC login.

Extend `MedLog/backend/tests/tests_oidc_mapping.py` for [Change 4](#change-4-sidequest-a-deactivated-oidc-user-must-be-refused):

* log in a **dedicated** mock user (new entry in `_OIDC_TEST_USERS`, its own `sub`, so no other
  test inherits a deactivated account), deactivate it via `PATCH /api/user/{id}` with
  `{"deactivated": true}` as admin, then log in again and assert 401 instead of a 500.
  `UserCRUD.update` uses `model_dump(exclude_unset=True)`, so patching only `deactivated` does
  not clear the user's roles.

Run with `./run_backend_tests_with_sqlite.sh` and `./run_backend_tests_with_postgres.sh`.

## Docs

* Regenerate `docs/configuration.md` with `./build_config_docs.sh` after the config change.
* `docs/PERMISSIONS.md`: add a short paragraph to the OIDC section stating that the client hides
  permission management when the mappings are in use, how the flag is derived, and the rename
  caveat (`STUDY_PERMISSION_MAPPING` is keyed by display name).

## Handover to the frontend work

Not implemented here (backend only), to be reported on the issue:

* The response field is `disable_ui_permission_management` (the issue body's
  `disable_ui_permission_managament` is a typo).
* The client should use the combination rule from the contract table, not the global flag alone.
* The `Deaktivieren` button on `/manage/users` is **not** covered by the flag, contrary to the
  issue body. See "`Deaktivieren` is deliberately not in that table" above for why.
* `Study` objects gained `is_oidc_permission_managed` and `oidc_managed_permissions`; the study
  rename dialog can use them for a warning.

## Follow-ups explicitly out of scope

* Hard-disabling permission management in the API (the api-key loophole from the issue thread).
  If wanted later, the natural shape is a separate setting, since
  `DISABLE_UI_PERMISSION_MANAGEMENT` promises a UI-only effect in its documentation.
* Refusing or warning on a rename of an OIDC-mapped study on the server side.
* Making `STUDY_PERMISSION_MAPPING` reference studies by id instead of display name, which would
  remove the rename problem at the root.
