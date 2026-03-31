from sqlmodel import Field, SQLModel
from enum import Enum
from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()


class AppState(SQLModel, table=True):
    key: str = Field(
        description="The name of the state we want to read/write", primary_key=True
    )
    value: str | None = Field(default=None, description="The actual value of the state")
