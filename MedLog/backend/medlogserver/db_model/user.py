from typing import AsyncGenerator, List, Optional


from medlogserver.db_model.base import Base

from sqlmodel import Field


class User(Base):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default=None, index=True)
    disabled: bool = Field(default=False)
    scopes: List[str] = Field(default=[])


class Device(Base):
    __tablename__ = "device"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default=None)
    user: User = Field(default=None, foreign_key="users.id")
    disabled: bool = Field(default=False)

class ClientToken(Base):
    