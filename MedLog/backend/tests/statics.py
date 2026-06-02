from pathlib import Path

DB_PATH = f"{Path(__file__).parent}/testdb.sqlite"
DOT_ENV_FILE_PATH = f"{Path(__file__).parent}/.env"
ADMIN_USER_NAME = "admin"
ADMIN_USER_PW = "password123"
ADMIN_USER_EMAIL = "user@test.de"
TEST_USER_NAME = "testuser01"
TEST_USER_PW = "testuserpw01"
DRUG_IMPORTER_ALLOW_MANUAL_UPDATE_DRUG_DB = True
SYSTEM_ANNOUNCEMENTS = [
    {"type": "info", "public": True, "message": "This is a public message"},
    {"type": "alert", "public": False, "message": "This is a non-public alert"},
]

# OIDC mock constants — consumed by tests_oidc_mapping.py and main.py
OIDC_TEST_PROVIDER_DISPLAY_NAME = "LocalTestOIDC"
OIDC_TEST_PROVIDER_SLUG = "localtestoidc"
OIDC_TEST_STUDY_NAME = "OidcPermissionTestStudy"
OIDC_TEST_ROLE_GROUP = "oidc-group-admins"
OIDC_TEST_INTERVIEWER_GROUP = "oidc-group-interviewers"
OIDC_TEST_STUDY_ADMIN_GROUP = "oidc-group-study-admins"
# A study name referenced in STUDY_PERMISSION_MAPPING that is intentionally never
# created in the DB — used to test the "unknown study" warning path.
OIDC_TEST_NONEXISTENT_STUDY_NAME = "OidcNonexistentTestStudy"
