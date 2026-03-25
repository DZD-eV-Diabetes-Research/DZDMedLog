from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from medlogserver.model.app_state import AppState
from medlogserver.model.unset import Unset, _Unset
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class AppStateCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        key: str,
        raise_if_key_missing: type[Exception] | None = None,
        default: str | None | _Unset = Unset,
    ) -> str | None:
        if raise_if_key_missing is not None and not isinstance(default, _Unset):
            raise ValueError("raise_if_missing and default are mutually exclusive")

        app_state = await self.session.get(AppState, key)

        if app_state is None:
            if raise_if_key_missing is not None:
                raise raise_if_key_missing()
            if not isinstance(default, _Unset):
                return default
            return None

        return app_state.value

    async def set(self, key: str, value: str | None) -> str | None:
        await self.session.merge(AppState(key=key, value=value))
        await self.session.commit()
        return value
