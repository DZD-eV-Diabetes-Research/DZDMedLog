# Basics
from typing import AsyncGenerator, List, Optional, Literal, Sequence

# Libs
import enum
import uuid
from pydantic import SecretStr
from sqlmodel import Field, Column, Enum, UniqueConstraint
from passlib.context import CryptContext

# Internal
from medlogserver.config import Config
from medlogserver.log import get_logger
from medlogserver.model._base_model import BaseTable
from medlogserver.model.user import User


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
    __table_args__ = (
        UniqueConstraint(
            "auth_source_type",
            "user_id",
            "oidc_provider_name",
            name="One auth entry only per user and permission provider.",
        ),
    )
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
