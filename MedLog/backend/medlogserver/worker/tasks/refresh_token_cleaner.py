"""Background task that removes auth records nobody can authenticate with anymore.

Rules (see issue #202):

- API tokens are deleted when they are revoked or expired, or when their source login
  (`api_token_source_user_auth_id`) is gone, revoked or expired. `get_current_user_auth`
  rejects all of them, and API token requests never refresh an OIDC login.
  Tokens from the token management (issue #198) have no source login, they are bound to
  the user and only deleted when revoked or expired.
- OIDC logins are deleted when they are revoked, or when their access token expired
  more than `AUTH_OIDC_EXPIRED_LOGIN_RETENTION_MINUTES` ago. Until then a browser
  session may still renew the access token via the refresh token, so an expired
  access token alone is no reason to delete the login.
  Exception: an OIDC login that is the source of an API token was created by the token
  login flow. Its session never reached a browser, so nothing can refresh it and it is
  deleted as soon as its access token expired.
- Sessions are deleted together with their login, when their login is gone already,
  when their basic login is revoked or expired, or when they expired and are not bound
  to an OIDC login (only OIDC sessions can be renewed).

Basic (password) logins are never deleted. They hold the user's password, and an admin
may reactivate them. Their sessions and API tokens are deleted though, so a reactivated
login does not bring old sessions and tokens back to life.
Sessions without an expiry date (basic password sessions) are kept as long as their
login is usable.
"""

from typing import Dict
import datetime

from sqlmodel import select, delete, col, or_, and_
from sqlalchemy.orm import aliased

#
from medlogserver.worker.task import TaskBase
from medlogserver.db._session import get_async_session_context
from medlogserver.model.user_auth import UserAuth, AllowedAuthSchemeType
from medlogserver.model.user_session import UserSession
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger(modulename="Task:TokenCleaner")
config = Config()


class AuthTokenCleaner:
    def __init__(self, now_epoch_time: int | None = None):
        self.now_epoch_time = (
            now_epoch_time
            if now_epoch_time is not None
            else int(datetime.datetime.now(tz=datetime.UTC).timestamp())
        )

    def _is_usable(self, login):
        """SQL condition: the login is neither revoked nor expired."""
        return and_(
            col(login.revoked).is_not(True),
            or_(
                col(login.expires_at_epoch_time).is_(None),
                col(login.expires_at_epoch_time) >= self.now_epoch_time,
            ),
        )

    def _obsolete_oidc_login_ids(self):
        oidc_expired_before = (
            self.now_epoch_time - config.AUTH_OIDC_EXPIRED_LOGIN_RETENTION_MINUTES * 60
        )
        token = aliased(UserAuth)
        token_source_login_ids = select(token.api_token_source_user_auth_id).where(
            token.auth_source_type == AllowedAuthSchemeType.api_token,
            col(token.api_token_source_user_auth_id).is_not(None),
        )
        return select(UserAuth.id).where(
            UserAuth.auth_source_type == AllowedAuthSchemeType.oidc,
            or_(
                col(UserAuth.revoked).is_(True),
                col(UserAuth.expires_at_epoch_time) < oidc_expired_before,
                and_(
                    col(UserAuth.expires_at_epoch_time) < self.now_epoch_time,
                    col(UserAuth.id).in_(token_source_login_ids),
                ),
            ),
        )

    async def remove_obsolete_auth_records(self) -> Dict[str, int]:
        """Deletes obsolete OIDC logins, API tokens and sessions in one transaction.

        Every delete states its conditions again instead of working on a list of ids
        fetched before. A login that gets refreshed by a request while the cleaner runs
        therefore no longer matches and survives.

        Returns:
            Dict[str, int]: Deleted row count per record type
        """
        async with get_async_session_context() as session:
            # Sessions go first. On PostgreSQL `user_session.user_auth_id` is an enforced
            # foreign key, so a login can not be deleted while a session still points at it.
            result = await session.exec(
                delete(UserSession).where(
                    col(UserSession.user_auth_id).in_(self._obsolete_oidc_login_ids())
                )
            )
            deleted_sessions = result.rowcount

            result = await session.exec(
                delete(UserAuth).where(
                    col(UserAuth.id).in_(self._obsolete_oidc_login_ids())
                )
            )
            deleted_oidc_logins = result.rowcount

            # Runs after the OIDC logins are gone, so tokens derived from them are caught
            # by the "source login is not usable" condition in the same pass.
            source_login = aliased(UserAuth)
            usable_source_login_ids = select(source_login.id).where(
                source_login.auth_source_type != AllowedAuthSchemeType.api_token,
                self._is_usable(source_login),
            )
            result = await session.exec(
                delete(UserAuth).where(
                    UserAuth.auth_source_type == AllowedAuthSchemeType.api_token,
                    or_(
                        col(UserAuth.revoked).is_(True),
                        col(UserAuth.expires_at_epoch_time) < self.now_epoch_time,
                        and_(
                            col(UserAuth.api_token_source_user_auth_id).is_not(None),
                            col(UserAuth.api_token_source_user_auth_id).not_in(
                                usable_source_login_ids
                            ),
                        ),
                    ),
                )
            )
            deleted_api_tokens = result.rowcount

            # Leftovers: sessions whose login vanished some other way (SQLite does not
            # enforce the foreign key), sessions of revoked or expired basic logins and
            # expired sessions that can not be renewed.
            oidc_login_ids = select(UserAuth.id).where(
                UserAuth.auth_source_type == AllowedAuthSchemeType.oidc
            )
            session_capable_login_ids = select(UserAuth.id).where(
                or_(
                    UserAuth.auth_source_type == AllowedAuthSchemeType.oidc,
                    self._is_usable(UserAuth),
                )
            )
            result = await session.exec(
                delete(UserSession).where(
                    or_(
                        col(UserSession.user_auth_id).not_in(session_capable_login_ids),
                        and_(
                            col(UserSession.expires_at_epoch_time) < self.now_epoch_time,
                            col(UserSession.user_auth_id).not_in(oidc_login_ids),
                        ),
                    )
                )
            )
            deleted_sessions += result.rowcount

            await session.commit()
        return {
            "sessions": deleted_sessions,
            "oidc_logins": deleted_oidc_logins,
            "api_tokens": deleted_api_tokens,
        }


class TaskCleanTokens(TaskBase):
    async def work(self):
        log.debug("Run Background Task: Clean tokens...")
        deleted = await AuthTokenCleaner().remove_obsolete_auth_records()
        summary = ", ".join(f"{count} {kind}" for kind, count in deleted.items())
        if any(deleted.values()):
            log.info(f"Removed obsolete auth records: {summary}")
        log.debug("Done Background Task: Clean tokens")
        return f"Deleted {summary}"
