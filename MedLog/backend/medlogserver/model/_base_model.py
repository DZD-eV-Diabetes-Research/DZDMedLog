from typing import Optional
from datetime import datetime
from pydantic import Field
from sqlalchemy import text
import uuid


from sqlmodel import SQLModel


from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()
import uuid


class MedLogBaseModel(SQLModel):
    # Abstaractiion layer for SQLModel to be able to introduce global changes later
    pass


""" 
# we can not outsource the primary key to a parent base model. sqlalchemy does not like that and throws an error in model init. e.g. 
# "sqlalchemy.exc.ArgumentError: Mapper Mapper[User(user)] could not assemble any primary key columns for mapped table 'user'"
# saaad. very saaaad.
class UUIDModel(SQLModel):
    pk: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
        ## sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )
"""


class TimestampModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    ## this is broken because fastapi/pydantic does not like the "sqlalchemy.text()" part.
    # todo: (with reasonable effort) find a solution to implement a way to implement an updated_at column/function.
    """
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={
            "onupdate": text("current_timestamp(0)"),
        },
    )
    """


class BaseTable(TimestampModel):
    pass
