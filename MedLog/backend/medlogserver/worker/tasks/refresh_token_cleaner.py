from typing import List
import datetime

#
from medlogserver.model.user_auth_refresh_token import UserAuthRefreshToken
from medlogserver.db.user_auth_refresh_token import UserAuthRefreshTokenCRUD
from medlogserver.db._session import get_async_session_context


class RefreshTokenCleaner:
    def __init__(self):
        pass

    async def remove_expired_tokens(self):
        async with get_async_session_context() as session:
            async with UserAuthRefreshTokenCRUD.crud_context(
                session
            ) as ai_version_crud:
                crud: UserAuthRefreshTokenCRUD = ai_version_crud
                tokens: List[UserAuthRefreshToken] = await crud.list()
                for token in tokens:
                    if (
                        token.valid_until_timestamp
                        < datetime.datetime.now(tz=datetime.UTC).timestamp()
                        or token.deactivated
                    ):
                        crud.delete(id=token.id)
