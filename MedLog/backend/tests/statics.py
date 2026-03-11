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
