"""Tests for the permission-management hint flags (issue #344).

The backend does not enforce anything here: it publishes two facts so the web client
can hide controls that OIDC would overwrite on the next login.

  * ``DISABLE_UI_PERMISSION_MANAGEMENT`` — global, derived from ROLE_MAPPING when unset.
  * ``Config.get_oidc_managed_study_permissions()`` — per study, from STUDY_PERMISSION_MAPPING.

In-process style (like tests_public_url.py): Config objects are built directly, no
live server involved.
"""

from medlogserver.config import Config


def _provider(**overrides) -> dict:
    """A minimally valid OIDC provider config, with the mapping under test patched in."""
    provider = {
        "PROVIDER_DISPLAY_NAME": overrides.pop("PROVIDER_DISPLAY_NAME", "TestProvider"),
        "CONFIGURATION_ENDPOINT": "https://idp.example.com/.well-known/openid-configuration",
        "CLIENT_ID": "test-client-id",
        "CLIENT_SECRET": "test-client-secret",
        "ROLE_MAPPING": {},
        "STUDY_PERMISSION_MAPPING": {},
    }
    provider.update(overrides)
    return provider


def build_config(**overrides) -> Config:
    """Build a Config with the OIDC settings under test passed explicitly.

    Constructor arguments outrank every environment source in pydantic-settings, so the
    test environment's own OIDC provider (set up by conftest for the live suite) does not
    leak into these cases. AUTH_OIDC_TOKEN_STORAGE_SECRET is always supplied because
    Config refuses a configured provider list without it.
    """
    overrides.setdefault("AUTH_OIDC_PROVIDERS", [])
    overrides.setdefault("AUTH_OIDC_TOKEN_STORAGE_SECRET", "test-storage-secret")
    return Config(**overrides)


# ── DISABLE_UI_PERMISSION_MANAGEMENT ──────────────────────────────────────────


def test_unset_without_oidc_provider_is_false():
    config = build_config()
    assert config.oidc_role_mapping_is_configured() is False
    assert config.is_ui_permission_management_disabled() is False


def test_unset_with_role_mapping_is_true():
    config = build_config(
        AUTH_OIDC_PROVIDERS=[_provider(ROLE_MAPPING={"idp-admins": ["medlog-admin"]})]
    )
    assert config.oidc_role_mapping_is_configured() is True
    assert config.is_ui_permission_management_disabled() is True


def test_unset_with_only_study_permission_mapping_is_false():
    """The global flag is derived from ROLE_MAPPING (global roles) only.

    STUDY_PERMISSION_MAPPING is reported per study instead, so each field keeps a single
    honest meaning and the client combines them. A provider that maps study permissions
    but no global roles must therefore not hide the global role management.
    """
    config = build_config(
        AUTH_OIDC_PROVIDERS=[
            _provider(
                STUDY_PERMISSION_MAPPING={
                    "SomeStudy": {"idp-interviewers": ["is_study_interviewer"]}
                }
            )
        ]
    )
    assert config.oidc_role_mapping_is_configured() is False
    assert config.is_ui_permission_management_disabled() is False


def test_explicit_false_beats_a_configured_role_mapping():
    config = build_config(
        DISABLE_UI_PERMISSION_MANAGEMENT=False,
        AUTH_OIDC_PROVIDERS=[_provider(ROLE_MAPPING={"idp-admins": ["medlog-admin"]})],
    )
    assert config.oidc_role_mapping_is_configured() is True
    assert config.is_ui_permission_management_disabled() is False


def test_explicit_true_without_any_oidc_provider():
    config = build_config(DISABLE_UI_PERMISSION_MANAGEMENT=True)
    assert config.is_ui_permission_management_disabled() is True


# ── get_oidc_managed_study_permissions ────────────────────────────────────────


def _two_provider_config() -> Config:
    return build_config(
        AUTH_OIDC_PROVIDERS=[
            _provider(
                PROVIDER_DISPLAY_NAME="ProviderOne",
                STUDY_PERMISSION_MAPPING={
                    "MappedStudy": {
                        "idp-interviewers": ["is_study_interviewer"],
                        # An unknown flag name must never reach the API response.
                        "idp-typo-group": ["is_study_wizard"],
                    }
                },
            ),
            _provider(
                PROVIDER_DISPLAY_NAME="ProviderTwo",
                STUDY_PERMISSION_MAPPING={
                    "MappedStudy": {"idp-study-admins": ["is_study_admin"]},
                    "OtherStudy": {"idp-viewers": ["is_study_viewer"]},
                },
            ),
        ]
    )


def test_managed_permissions_are_the_sorted_union_across_providers():
    config = _two_provider_config()
    assert config.get_oidc_managed_study_permissions("MappedStudy") == [
        "is_study_admin",
        "is_study_interviewer",
    ]


def test_managed_permissions_drop_unknown_flag_names():
    config = _two_provider_config()
    assert "is_study_wizard" not in config.get_oidc_managed_study_permissions(
        "MappedStudy"
    )


def test_managed_permissions_are_empty_for_an_unmapped_study():
    config = _two_provider_config()
    assert config.get_oidc_managed_study_permissions("NotInAnyMapping") == []


def test_managed_permissions_are_empty_after_a_rename():
    """The mapping is keyed by the study's display name and matched exactly.

    Renaming a mapped study silently detaches it from the mapping (mirroring
    StudyCRUD.get_by_name). This is the case the client is supposed to warn about
    before a rename, so pin the behaviour here.
    """
    config = _two_provider_config()
    assert config.get_oidc_managed_study_permissions("MappedStudy ") == []
    assert config.get_oidc_managed_study_permissions("mappedstudy") == []
    assert config.get_oidc_managed_study_permissions("MappedStudy (renamed)") == []


def test_managed_permissions_without_any_oidc_provider():
    config = build_config()
    assert config.get_oidc_managed_study_permissions("AnyStudy") == []
