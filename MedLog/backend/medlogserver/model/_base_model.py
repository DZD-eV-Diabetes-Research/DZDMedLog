from typing import Optional
import datetime
from pydantic import field_validator, ValidationInfo, BaseModel
from sqlalchemy import text
from sqlmodel import Field
import uuid


import sqlmodel.main
from sqlmodel import SQLModel


from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()
import uuid


# sqlmodel >= 0.0.32 attaches a `FieldInfoMetadata` instance to every `Field()`.
# It is a plain `@dataclass`, so Python generates `__eq__` and sets `__hash__` to
# `None` -> any `Annotated[..., FieldInfoMetadata(...)]` becomes unhashable. FastAPI's
# OpenAPI generation collects those annotations into a set
# (`fastapi/_compat/v2.py: input_types = {f.field_info.annotation for f in fields}`)
# and dies with `TypeError: unhashable type: 'FieldInfoMetadata'`.
# In our case this is triggered by class-as-dependency params (`= Depends()`) on
# SQLModel models, which FastAPI expands into individual route fields.
#
# Restoring identity-based hashing is safe: sqlmodel never puts these objects into a
# set or dict, it only scans `field_info.metadata` with `isinstance()`. Note that the
# obvious alternatives `@dataclass(unsafe_hash=True)` / `frozen=True` would NOT work
# here, because they hash the field tuple - which contains `sa_column_kwargs` dicts.
#
# Neither fastapi nor sqlmodel have fixed this upstream (both proposed PRs were closed
# by the stale bot without merging: sqlmodel#1889, fastapi#15429). Verified still broken
# with fastapi 0.141.1 / sqlmodel 0.0.39 / pydantic 2.13.4.
# See https://github.com/DZD-eV-Diabetes-Research/DZDMedLog/issues/226
sqlmodel.main.FieldInfoMetadata.__hash__ = object.__hash__


class MedLogBaseApiModel(BaseModel):
    # Absolute base class for all api only models. All api only model classes will inherhit from this class.
    pass


class MedLogBaseModel(SQLModel):
    # Absolute database and api base class. All model classes will inherhit from this class.

    # cast all ids to UUIDs
    @field_validator("id", check_fields=False)
    @classmethod
    def id_to_uuid(cls, v: str | uuid.UUID, info: ValidationInfo) -> uuid.UUID:
        if isinstance(v, str):
            v = uuid.UUID(v)
        return v


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


get_now_datetime_witout_timezone = lambda: datetime.datetime.now(
    tz=datetime.timezone.utc
).replace(tzinfo=None)


class TimestampModel(SQLModel):
    created_at: datetime.datetime = Field(
        default_factory=get_now_datetime_witout_timezone,
        nullable=False,
    )

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


class BaseTable(SQLModel):
    pass


class ExportBaseModel(MedLogBaseModel):
    created_at: datetime.datetime = Field(exclude=True)
