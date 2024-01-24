from typing import AsyncGenerator, List, Optional, Literal, Sequence
from pydantic import SecretStr, Json
from fastapi import Depends
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable
from medlogserver.db.base import AsyncSession, get_session
from sqlmodel import Field, select, delete
from uuid import UUID
from passlib.context import CryptContext

log = get_logger()
config = Config()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# UserAuth Models and Table
class _UserAuthBase(BaseTable, table=False):
    user_id: UUID = Field(foreign_key="user.id")
    auth_source: Literal["local", "oidc"] = Field()
    oidc_provider_name: str = Field(default=None, index=True)


class UserAuthUpdate(BaseTable, table=False):
    password: SecretStr = Field(
        default=None,
        min_length=10,
        description="The password of the user. Can be None if user is authorized by external provider. e.g. OIDC",
    )


class UserAuthCreate(_UserAuthBase, UserAuthUpdate, table=False):
    pass


class UserAuth(_UserAuthBase, table=True):
    __tablename__ = "user_auth"
    password_hashed: SecretStr = Field(
        default=None,
        description="The hashed password of the user. Can be None if user is authorized by external provider. e.g. OIDC",
    )

    def verify_password(self, password: SecretStr) -> bool:
        return pwd_context.verify(
            password.get_secret_value(), self.password_hashed.get_secret_value()
        )


class UserAuthCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user(
        self,
        user_id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuth]:
        query = select(UserAuth).where(UserAuth.user_id == user_id)

        results = await self.session.exec(statement=query)
        user: UserAuth | None = results.all()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def create(self, user_auth_create: UserAuthCreate) -> UserAuth:
        password_hashed = pwd_context.hash(user_auth_create.password.get_secret_value())
        user_vals = {}
        for k, v in user_auth_create.model_dump().items():
            if k != "password":
                setattr(user_vals, "password_hashed", password_hashed)
            else:
                setattr(user_vals, k, v)
        user_auth = UserAuth(**user_vals)
        self.session.add(user_auth)
        await self.session.commit()
        await self.session.refresh(user_auth)
        return user_auth

    async def delete(
        self, id: str | UUID, raise_exception_if_not_exists=None
    ) -> None | Literal[True]:
        user_auth = select(UserAuth).where(UserAuth.id == id)
        if user_auth is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        else:
            query = delete(UserAuth).where(UserAuth.id == id)
            await self.session.exec(statement=query)
            await self.session.commit()
            return True

    async def update(
        self,
        user_auth_update: UserAuthUpdate,
        id: str | UUID = None,
    ) -> UserAuth:
        id = id if id is not None else user_auth_update.id
        if id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        user_auth = select(UserAuth).where(UserAuth.id == id)
        password_hashed = pwd_context.hash(user_auth_update.password.get_secret_value())
        for k, v in user_auth_update.model_dump(exclude_unset=True).items():
            if k != "password":
                setattr(user_auth, "password_hashed", password_hashed)
            else:
                # this is unused code for now, as it is only possible to change the password. but maybe we add more attributes later to the UserAuthUpdate class
                setattr(user_auth, k, v)
        self.session.add(user_auth)
        await self.session.commit()
        await self.session.refresh(user_auth)
        return user_auth


async def get_user_auth_crud(
    session: AsyncSession = Depends(get_session),
) -> UserAuthCRUD:
    return UserAuthCRUD(session=session)


# ClientAccessToken models and table


class _UserAuthAccessTokenBase(BaseTable, table=False):
    __tablename__ = "user_auth_access_token"
    user_id: UUID = Field(default=None, foreign_key="user.id")


class UserAuthAccessTokenUpdate(_UserAuthAccessTokenBase, table=False):
    disabled: bool = Field(default=False)


class UserAuthAccessTokenCreate(_UserAuthAccessTokenBase, table=False):
    token_encoded: str = Field()
    valid_until_timestamp: int = Field(default=None)


class UserAuthAccessToken(
    UserAuthAccessTokenCreate, UserAuthAccessTokenUpdate, table=True
):
    __tablename__ = "user_auth_access_token"


class UserAuthAccessTokenCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        id: str | UUID,
        raise_exception_if_none: Exception = None,
    ) -> UserAuthAccessToken:
        query = select(UserAuthAccessToken).where(UserAuthAccessToken.id == id)

        results = await self.session.exec(statement=query)
        user_auth_access_token: UserAuthAccessToken | None = results.one_or_none()
        if user_auth_access_token is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user_auth_access_token

    async def list_by_user(
        self,
        user_id: str | UUID,
    ) -> List[UserAuthAccessToken]:
        query = select(UserAuthAccessToken).where(
            UserAuthAccessToken.user_id == user_id
        )
        results = await self.session.exec(statement=query)
        user_auth_access_tokens: Sequence[UserAuthAccessToken] = results.all()

        return list(user_auth_access_tokens)

    async def create(
        self, user_auth_access_token_create: UserAuthAccessTokenCreate
    ) -> UserAuthAccessToken:
        user_auth_access_token = UserAuthAccessToken(
            **user_auth_access_token_create.model_dump()
        )
        self.session.add(user_auth_access_token)
        await self.session.commit()
        await self.session.refresh(user_auth_access_token)
        return user_auth_access_token

    async def delete(
        self, id: str | UUID, raise_exception_if_not_exists=None
    ) -> None | Literal[True]:
        query = select(UserAuthAccessToken).where(UserAuthAccessToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth = results.one_or_none()

        if user_auth is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        else:
            query = delete(UserAuthAccessToken).where(UserAuthAccessToken.id == id)
            await self.session.exec(statement=query)
            await self.session.commit()
            return True

    async def update(
        self,
        user_auth_access_token_update: UserAuthAccessTokenUpdate,
        id: str | UUID = None,
    ) -> UserAuthAccessToken:
        id = id if id is not None else user_auth_access_token_update.id
        if id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        query = select(UserAuthAccessToken).where(UserAuthAccessToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth_access_token = results.one_or_none()
        assert (
            user_auth_access_token.user_id == user_auth_access_token_update.user_id
        ), "user_id foreign key must not be changed on token update"
        for k, v in user_auth_access_token_update.model_dump(
            exclude_unset=True
        ).items():
            setattr(user_auth_access_token, k, v)

        self.session.add(user_auth_access_token)
        await self.session.commit()
        await self.session.refresh(user_auth_access_token)
        return user_auth_access_token


async def get_user_auth_access_token_crud(
    session: AsyncSession = Depends(get_session),
) -> UserAuthAccessTokenCRUD:
    return UserAuthAccessTokenCRUD(session=session)
