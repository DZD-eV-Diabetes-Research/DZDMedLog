"""Tests for the background token cleaner (issue #202).

The cleaner deletes rows directly with SQL, so these tests seed every kind of auth
record into a throwaway SQLite database and check which ones survive. Like
`tests_drug_data_cleanup.py` they run twice:

- `foreign_keys=OFF` mirrors SQLite deployments, where orphaned sessions can exist.
- `foreign_keys=ON`  mirrors PostgreSQL, where deleting a login that a session still
  points at aborts the transaction. This catches a wrong delete order.
"""

from typing import Dict
import asyncio
import os
import uuid

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from medlogserver.model.__tables__ import all_tables  # noqa: F401  (registers metadata)
from medlogserver.model.user import User
from medlogserver.model.user_auth import UserAuth, AllowedAuthSchemeType
from medlogserver.model.user_session import UserSession

NOW = 1_800_000_000
RETENTION_MIN = 60
HOUR = 60 * 60


@pytest.fixture(params=[False, True], ids=["fk_off", "fk_on"])
def isolated_db(request, tmp_path, monkeypatch):
    """An empty MedLog schema in a throwaway SQLite file, wired into the db layer."""
    enforce_foreign_keys = request.param
    db_file = tmp_path / "token_cleaner_test.sqlite"

    SQLModel.metadata.create_all(create_engine(f"sqlite:///{db_file}"))

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}", future=True, poolclass=NullPool
    )
    if enforce_foreign_keys:

        @event.listens_for(engine.sync_engine, "connect")
        def _enable_foreign_keys(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    from medlogserver.db import _session
    from medlogserver.worker.tasks import refresh_token_cleaner

    monkeypatch.setattr(_session, "_db_engine", engine)
    monkeypatch.setattr(
        _session,
        "_async_session_factory",
        sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autoflush=False),
    )
    # keeps _get_engine() from replacing our engine with the one from the config
    monkeypatch.setattr(_session, "_engine_pid", os.getpid())
    monkeypatch.setattr(
        refresh_token_cleaner.config,
        "AUTH_OIDC_EXPIRED_LOGIN_RETENTION_MINUTES",
        RETENTION_MIN,
    )

    yield enforce_foreign_keys

    asyncio.run(engine.dispose())


def _auth(user: User, source: AllowedAuthSchemeType, **kwargs) -> UserAuth:
    return UserAuth(id=uuid.uuid4(), user_id=user.id, auth_source_type=source, **kwargs)


def _session_for(auth: UserAuth, **kwargs) -> UserSession:
    return UserSession(id=uuid.uuid4(), user_id=auth.user_id, user_auth_id=auth.id, **kwargs)


async def _seed(session, with_orphan_session: bool) -> Dict[str, uuid.UUID]:
    """Seeds one record per case. Keys starting with `keep_` must survive a cleaner run."""
    user = User(id=uuid.uuid4(), user_name="token-cleaner-test-user")
    session.add(user)
    await session.commit()

    basic = _auth(user, AllowedAuthSchemeType.basic)
    basic_expired = _auth(
        user, AllowedAuthSchemeType.basic, expires_at_epoch_time=NOW - HOUR
    )
    basic_revoked = _auth(user, AllowedAuthSchemeType.basic, revoked=True)
    oidc_valid = _auth(
        user, AllowedAuthSchemeType.oidc, expires_at_epoch_time=NOW + HOUR
    )
    # access token expired, but still within the retention period: may be refreshed
    oidc_refreshable = _auth(
        user,
        AllowedAuthSchemeType.oidc,
        expires_at_epoch_time=NOW - RETENTION_MIN * 60 + 10,
    )
    oidc_outdated = _auth(
        user,
        AllowedAuthSchemeType.oidc,
        expires_at_epoch_time=NOW - RETENTION_MIN * 60 - 10,
    )
    # created by the token login flow: no browser session can ever refresh it
    oidc_token_source_expired = _auth(
        user, AllowedAuthSchemeType.oidc, expires_at_epoch_time=NOW - 10
    )
    oidc_revoked = _auth(
        user,
        AllowedAuthSchemeType.oidc,
        expires_at_epoch_time=NOW + HOUR,
        revoked=True,
    )
    records = {
        "keep_basic": basic,
        "keep_basic_expired": basic_expired,
        "keep_basic_revoked": basic_revoked,
        "keep_oidc_valid": oidc_valid,
        "keep_oidc_refreshable": oidc_refreshable,
        "del_oidc_outdated": oidc_outdated,
        "del_oidc_revoked": oidc_revoked,
        "del_oidc_token_source_expired": oidc_token_source_expired,
    }
    session.add_all(records.values())
    await session.commit()

    token = AllowedAuthSchemeType.api_token
    records |= {
        "keep_token_valid": _auth(
            user, token, api_token_source_user_auth_id=basic.id, expires_at_epoch_time=NOW + HOUR
        ),
        "keep_token_no_expiry": _auth(user, token, api_token_source_user_auth_id=basic.id),
        "keep_token_without_source": _auth(user, token, expires_at_epoch_time=NOW + HOUR),
        "keep_token_of_valid_oidc": _auth(
            user, token, api_token_source_user_auth_id=oidc_valid.id
        ),
        "del_token_expired": _auth(
            user, token, api_token_source_user_auth_id=basic.id, expires_at_epoch_time=NOW - 1
        ),
        "del_token_revoked": _auth(
            user, token, api_token_source_user_auth_id=basic.id, revoked=True
        ),
        "del_token_source_missing": _auth(
            user, token, api_token_source_user_auth_id=uuid.uuid4()
        ),
        "del_token_of_outdated_oidc": _auth(
            user, token, api_token_source_user_auth_id=oidc_outdated.id
        ),
        "del_token_of_revoked_oidc": _auth(
            user, token, api_token_source_user_auth_id=oidc_revoked.id
        ),
        "del_token_of_expired_oidc": _auth(
            user, token, api_token_source_user_auth_id=oidc_token_source_expired.id
        ),
        "del_token_of_expired_basic": _auth(
            user, token, api_token_source_user_auth_id=basic_expired.id
        ),
        "del_token_of_revoked_basic": _auth(
            user, token, api_token_source_user_auth_id=basic_revoked.id
        ),
        "keep_session_basic": _session_for(basic),
        "keep_session_oidc_valid": _session_for(
            oidc_valid, expires_at_epoch_time=NOW + HOUR
        ),
        "keep_session_oidc_refreshable": _session_for(
            oidc_refreshable, expires_at_epoch_time=NOW - HOUR
        ),
        "del_session_basic_expired": _session_for(basic, expires_at_epoch_time=NOW - 1),
        "del_session_oidc_outdated": _session_for(
            oidc_outdated, expires_at_epoch_time=NOW - RETENTION_MIN * 60 - 10
        ),
        "del_session_oidc_revoked": _session_for(
            oidc_revoked, expires_at_epoch_time=NOW + HOUR
        ),
        "del_session_oidc_token_source_expired": _session_for(
            oidc_token_source_expired, expires_at_epoch_time=NOW - 10
        ),
        "del_session_of_expired_basic": _session_for(basic_expired),
        "del_session_of_revoked_basic": _session_for(basic_revoked),
    }
    if with_orphan_session:
        records["del_session_orphaned"] = _session_for(
            _auth(user, AllowedAuthSchemeType.basic)
        )
    session.add_all(records.values())
    await session.commit()
    return {name: record.id for name, record in records.items()}


async def _existing_ids(session) -> set:
    auth_ids = (await session.exec(select(UserAuth.id))).all()
    session_ids = (await session.exec(select(UserSession.id))).all()
    return set(auth_ids) | set(session_ids)


def test_token_cleaner_removes_only_obsolete_auth_records(isolated_db):
    from medlogserver.db._session import get_async_session_context
    from medlogserver.worker.tasks.refresh_token_cleaner import AuthTokenCleaner

    fk_enforced = isolated_db

    async def scenario():
        async with get_async_session_context() as session:
            seeded = await _seed(session, with_orphan_session=not fk_enforced)

        deleted = await AuthTokenCleaner(now_epoch_time=NOW).remove_obsolete_auth_records()

        async with get_async_session_context() as session:
            existing = await _existing_ids(session)
        wrongly_deleted = [n for n, i in seeded.items() if n.startswith("keep_") and i not in existing]
        not_deleted = [n for n, i in seeded.items() if n.startswith("del_") and i in existing]
        assert not wrongly_deleted, f"Cleaner deleted records it must keep: {wrongly_deleted}"
        assert not not_deleted, f"Cleaner left obsolete records: {not_deleted}"

        expected_session_count = 6 + (0 if fk_enforced else 1)
        assert deleted == {
            "sessions": expected_session_count,
            "oidc_logins": 3,
            "api_tokens": 8,
        }, deleted

        # a second run has nothing left to do
        deleted_again = await AuthTokenCleaner(now_epoch_time=NOW).remove_obsolete_auth_records()
        assert not any(deleted_again.values()), deleted_again

    asyncio.run(scenario())


def test_token_cleaner_task_reports_result(isolated_db):
    from medlogserver.worker.tasks.refresh_token_cleaner import TaskCleanTokens

    result = asyncio.run(TaskCleanTokens().work())
    assert result == "Deleted 0 sessions, 0 oidc_logins, 0 api_tokens"
