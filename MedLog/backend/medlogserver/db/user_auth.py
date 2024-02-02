# Basics
from typing import AsyncGenerator, List, Optional, Literal, Sequence

# Libs
import enum
import uuid
import contextlib
from pydantic import SecretStr, Json
from fastapi import Depends, HTTPException, status
from sqlmodel import Field, select, delete, Enum, Column
from passlib.context import CryptContext

# Internal
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.db.base import BaseTable
from medlogserver.db._session import AsyncSession, get_async_session
from medlogserver.db.user import User


log = get_logger()
config = Config()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AllowedAuthSourceTypes(str, enum.Enum):
    local = "local"
    oidc = "oidc"


# UserAuth Models and Table
class _UserAuthBase(BaseTable, table=False):
    user_id: uuid.UUID = Field(foreign_key="user.id")
    auth_source_type: AllowedAuthSourceTypes = Field(
        default="local", sa_column=Column(Enum(AllowedAuthSourceTypes))
    )
    oidc_provider_name: Optional[str] = Field(default=None, index=True)


class UserAuthUpdate(BaseTable, table=False):
    password: Optional[SecretStr] = Field(
        default=None,
        min_length=10,
        description="The password of the user. Can be None if user is authorized by external provider. e.g. OIDC",
    )


class UserAuthCreate(_UserAuthBase, UserAuthUpdate, table=False):
    pass


class UserAuth(_UserAuthBase, table=True):
    """This table stores the information of what type a certain user is and how the user can access our application.
    Either a user is of "local"-type and can login with the (hashed) password in this table or a user is external.
    External user are only comming from a OpenID Connect Provider at the moment and are maked as "oidc". Later there maybe "ldap" user as well.
    External users may have an extra table to store further auth informations. For oidc users that table is in medlogserver/db/user_auth_external_oidc_token.py

    Args:
        _UserAuthBase (_type_): _description_
        table (bool, optional): _description_. Defaults to True.

    Raises:
        raise_exception_if_wrong_pw: _description_

    Returns:
        _type_: _description_
    """

    __tablename__ = "user_auth"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
    password_hashed: Optional[str] = Field(
        default=None,
        description="The hashed password of the user. Can be None if user is authorized by external provider. e.g. OIDC",
    )

    def verify_password(
        self, password: SecretStr | str, raise_exception_if_wrong_pw: Exception = None
    ) -> bool:
        pw = password
        if isinstance(password, SecretStr):
            pw = password.get_secret_value()
        password_correct = pwd_context.verify(pw, self.password_hashed)
        if not password_correct and raise_exception_if_wrong_pw:
            raise raise_exception_if_wrong_pw
        return password_correct


class UserAuthCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_user_id(
        self,
        user_id: str | uuid.UUID,
        filter_auth_source_type: AllowedAuthSourceTypes = None,
        filter_oidc_provider_name: str = None,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuth]:
        query = select(UserAuth).where(UserAuth.user_id == user_id)
        if filter_auth_source_type:
            query.where(UserAuth.auth_source_type == filter_auth_source_type)
        if filter_oidc_provider_name:
            query.where(UserAuth.oidc_provider_name == filter_oidc_provider_name)
        results = await self.session.exec(statement=query)
        user_auths: Sequence[UserAuth] = results.all()
        if user_auths is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user_auths

    async def list_by_user_name(
        self,
        user_name: str | uuid.UUID,
        filter_auth_source_type: AllowedAuthSourceTypes = None,
        filter_oidc_provider_name: str = None,
        raise_exception_if_none: Exception = None,
    ) -> Sequence[UserAuth]:
        query = select(UserAuth).join(User).where(User.user_name == user_name)
        if filter_auth_source_type:
            query.where(UserAuth.auth_source_type == filter_auth_source_type)
        if filter_oidc_provider_name:
            query.where(UserAuth.oidc_provider_name == filter_oidc_provider_name)
        results = await self.session.exec(statement=query)
        user: UserAuth | None = results.all()
        if user is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user

    async def get_local_auth_source_by_user_id(
        self, user_id: str | uuid.UUID, raise_exception_if_none: Exception = None
    ) -> UserAuth | None:
        query = select(UserAuth).where(UserAuth.user_id == user_id)
        results = await self.session.exec(statement=query)
        user_auths: Sequence[UserAuth] | None = results.all()

        # for good measure we do a sanity check here. one user should only have one "local"-auth entry with a hashed password.
        if len(user_auths) > 1:
            # there are multiple local user auths. something is broken. Lets attach an uuid to the error, so we can identify it, if a user reports that.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details="Something went wrong. Please report this error. Error-id: f5d08a40-6d2e-442f-bd97-b0e3d0f9a2b7",
            )
        elif len(user_auths) == 0:
            if raise_exception_if_none:
                raise raise_exception_if_none
            return None
        user_auth = user_auths[0]
        return user_auth

    async def get_local_auth_source_by_user_name(
        self, user_name: str, raise_exception_if_none: Exception = None
    ) -> UserAuth | None:
        query = select(User).where(User.user_name == user_name)
        results = await self.session.exec(statement=query)
        user: User | None = results.one_or_none()
        if not user and raise_exception_if_none:
            raise raise_exception_if_none
        return await self.get_local_auth_source_by_user_id(user.id)

    async def create(self, user_auth_create: UserAuthCreate) -> UserAuth:
        password_hashed = None
        if user_auth_create.auth_source_type == AllowedAuthSourceTypes.local:
            if user_auth_create.password is None:
                raise ValueError("Password is not allowd to be empty for local users")
            password_hashed = pwd_context.hash(
                user_auth_create.password.get_secret_value()
            )

        user_vals = {}

        for k, v in user_auth_create.model_dump().items():
            log.info(f"{k} {v}")
            if k == "password":
                user_vals["password_hashed"] = password_hashed

            else:
                user_vals[k] = v

        log.debug(f"user_vals {user_vals}")
        user_auth = UserAuth(**user_vals)
        log.debug(user_auth)

        self.session.add(user_auth)
        await self.session.commit()
        await self.session.refresh(user_auth)
        return user_auth

    async def delete(
        self, id: str | uuid.UUID, raise_exception_if_not_exists=None
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
        id: str | uuid.UUID = None,
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
    session: AsyncSession = Depends(get_async_session),
) -> UserAuthCRUD:
    yield UserAuthCRUD(session=session)


get_user_auth_crud_context = contextlib.asynccontextmanager(get_user_auth_crud)

# ClientAccessToken models and table


class _UserAuthRefreshTokenBase(BaseTable, table=False):
    __tablename__ = "user_auth_access_token"
    user_auth_id: uuid.UUID = Field(default=None, foreign_key="user_auth.id")


class UserAuthRefreshTokenUpdate(_UserAuthRefreshTokenBase, table=False):
    deactivated: bool = Field(default=False)


class UserAuthRefreshTokenCreate(_UserAuthRefreshTokenBase, table=False):
    token_encoded: str = Field()
    valid_until_timestamp: int = Field(default=None)


class UserAuthRefreshToken(
    UserAuthRefreshTokenCreate, UserAuthRefreshTokenUpdate, table=True
):
    __tablename__ = "user_auth_access_token"
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        # sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class UserAuthRefreshTokenCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        id: str | uuid.UUID,
        show_deactivated: bool = False,
        raise_exception_if_none: Exception = None,
    ) -> UserAuthRefreshToken:
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        if not show_deactivated:
            query.where(UserAuthRefreshToken.deactivated == False)
        results = await self.session.exec(statement=query)
        user_auth_refresh_token: UserAuthRefreshToken | None = results.one_or_none()
        if user_auth_refresh_token is None and raise_exception_if_none:
            raise raise_exception_if_none
        return user_auth_refresh_token

    async def list_by_user(
        self,
        user_id: str | uuid.UUID,
    ) -> List[UserAuthRefreshToken]:
        query = select(UserAuthRefreshToken).where(
            UserAuthRefreshToken.user_id == user_id
        )
        results = await self.session.exec(statement=query)
        user_auth_refresh_tokens: Sequence[UserAuthRefreshToken] = results.all()

        return list(user_auth_refresh_tokens)

    async def create(
        self, user_auth_access_token_create: UserAuthRefreshTokenCreate
    ) -> UserAuthRefreshToken:
        user_auth_refresh_token = UserAuthRefreshToken(
            **user_auth_access_token_create.model_dump()
        )
        self.session.add(user_auth_refresh_token)
        await self.session.commit()
        await self.session.refresh(user_auth_refresh_token)
        return user_auth_refresh_token

    async def delete(
        self, id: str | uuid.UUID, raise_exception_if_not_exists=None
    ) -> None | Literal[True]:
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth = results.one_or_none()

        if user_auth is None and raise_exception_if_not_exists:
            raise raise_exception_if_not_exists
        else:
            query = delete(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
            await self.session.exec(statement=query)
            await self.session.commit()
            return True

    async def update(
        self,
        user_auth_access_token_update: UserAuthRefreshTokenUpdate,
        id: str | uuid.UUID = None,
    ) -> UserAuthRefreshToken:
        id = id if id is not None else user_auth_access_token_update.id
        if id is None:
            raise ValueError(
                "User update failed, uuid must be set in user_update or passed as argument `id`"
            )
        query = select(UserAuthRefreshToken).where(UserAuthRefreshToken.id == id)
        results = await self.session.exec(statement=query)
        user_auth_refresh_token: UserAuthRefreshToken = results.one_or_none()
        for k, v in user_auth_access_token_update.model_dump(
            exclude_unset=True
        ).items():
            if k in UserAuthRefreshTokenUpdate.model_fields.keys():
                setattr(user_auth_refresh_token, k, v)

        self.session.add(user_auth_refresh_token)
        await self.session.commit()
        await self.session.refresh(user_auth_refresh_token)
        return user_auth_refresh_token

    async def disable_by_user_id(self, user_id: uuid.UUID):
        """Disable all refresh token from a certain user

        Args:
            user_id (uuid.UUID): _description_

        Returns:
            _type_: _description_
        """
        query_tokens = (
            select(UserAuthRefreshToken)
            .join(UserAuth)
            .where(UserAuth.user_id == user_id)
        )
        results = await self.session.exec(statement=query_tokens)
        tokens: Sequence[UserAuthRefreshToken] = results.all()
        for token in tokens:
            token.deactivated = True
            self.session.add(token)
        self.session.commit()


async def get_user_auth_refresh_token_crud(
    session: AsyncSession = Depends(get_async_session),
) -> UserAuthRefreshTokenCRUD:
    yield UserAuthRefreshTokenCRUD(session=session)


get_user_auth_refresh_token_crud_context = contextlib.asynccontextmanager(
    get_user_auth_refresh_token_crud
)
