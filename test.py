from typing import AsyncGenerator, List, Optional, Literal, Sequence


def determine_class():
    from pydantic import BaseModel, Field

    class UserBase(BaseModel):
        email: Optional[str] = Field(default=None)

    class UserCreate(UserBase):
        user_name: Optional[str] = Field(default=None)

    u1 = UserCreate(email="bla", user_name="bla2")
    print(isinstance(u1, UserBase))
    print(type(u1) is UserBase)
    print(type(u1) is UserCreate)

    ub1 = UserBase(email="blp")
    u2 = UserCreate(**ub1.model_dump())
    print(u2)


def use_pydantic_emailstr_manually():
    from pydantic import EmailStr, validate_email
    from pydantic_core import PydanticCustomError

    from email_validator.exceptions_types import EmailNotValidError, EmailSyntaxError

    try:
        validate_email("rightmail@domain.com")
        validate_email("wrongmail.domain.com")
    except PydanticCustomError as er:
        print(er.message())
        print("EMAIL NOT GUT")

    use_pydantic_emailstr_manually()


def test_pzn_cleaner():
    def clean_pzn(pzn: str):
        return pzn.lstrip("PZN").replace("-", "").replace(" ", "")

    def test_clean_pzn():
        test_values = [
            ("PZN12345678", "12345678"),
            ("PZN-98765432", "98765432"),
            ("PZN - 55555555", "55555555"),
            ("PZN - 123-456-789", "123456789"),  # Keine führende "PZN-" entfernen
            ("PZN - ", ""),  # Keine Ziffern vorhanden
            ("123456789", "123456789"),  # Kein führendes "PZN" vorhanden
            ("PZN-11112222", "11112222"),  # Entfernt führendes "-PZN-"
            ("PZN - 3333-444-555", "3333444555"),  # Kein führendes "PZN-" entfernen
            ("PZN", ""),  # Keine Ziffern vorhanden
            ("PZN - 9876 - 5432", "98765432"),  # Kein führendes "PZN-" entfernen
        ]

        for input_value, expected_output in test_values:
            result = clean_pzn(input_value)
            assert (
                result == expected_output
            ), f"Error for input '{input_value}': Expected '{expected_output}', but got '{result}'."

    # Run the test
    test_clean_pzn()


def pathcombiner():

    from typing import List
    from pathlib import Path, PurePath

    def to_path(
        *args: str | Path | PurePath, absolute: bool = True, expanduser: bool = True
    ) -> Path:
        result_path_fragments: List[Path] = []
        for arg in args:
            if isinstance(arg, str):
                result_path_fragments.append(Path(arg))
            elif isinstance(arg, PurePath):
                result_path_fragments.append(arg)
            elif isinstance(arg, PurePath):
                result_path_fragments.append(Path(arg))
        result_path = Path.joinpath(*result_path_fragments)
        if expanduser:
            result_path = result_path.expanduser()
        if absolute:
            result_path = result_path.absolute()
        return result_path

    print(to_path("~", Path("test"), Path("thing/"), "filename.txt"))


def sqlmodel_class_field_extradata():
    # Sondercodes
    import uuid
    from sqlmodel import Field, SQLModel
    from sqlalchemy import String, Integer, Column, SmallInteger

    def custom_field(*args, source_file_csv_index=None, **kwargs):
        # Modify kwargs to include your custom parameters
        source_file_csv_index = kwargs.pop("source_file_csv_index", None)

        fieldinfo = Field(*args, **kwargs)
        print(type(fieldinfo))
        fieldinfo.source_file_csv_index = source_file_csv_index
        # Pass the modified kwargs to the sqlmodel.Field constructor
        return fieldinfo

    class Sondercodes(SQLModel, table=True):
        __tablename__ = "drug_sonder"
        gkvai_source_csv_filename: str = "sonder.txt"
        dateiversion: str = Field(
            description="Dateiversion",
            sa_type=String(3),
            sa_column_kwargs={"comment": "gkvai_source_csv_col_index:0"},
            primary_key=True,
        )
        datenstand: str = Field(
            description="Monat Datenstand (JJJJMM)",
            sa_type=String(6),
            sa_column_kwargs={"comment": "gkvai_source_csv_col_index:1"},
            primary_key=True,
        )
        pzn: str = Field(
            description="Pharmazentralnummer",
            sa_column_kwargs={"comment": "gkvai_source_csv_col_index:3"},
            sa_type=String(8),
            primary_key=True,
        )

    print(Sondercodes)
    for name, field in Sondercodes.model_fields.items():
        csv_source = None
        try:
            csv_source = int(
                getattr(field, "sa_column_kwargs", None)["comment"].split(":")[1]
            )
        except TypeError:
            pass
        print("csv_source", type(csv_source), csv_source)


# sqlmodel_class_field_extradata()
def seperate_string():
    import shlex

    def separate_words_with_quotes(input_string: str):
        return shlex.split(input_string)
        # Define a regular expression pattern to match quoted and non-quoted substrings
        pattern = re.compile(r"((\"[^\"]+\")|(-[^\s]+))")

        # Use findall to extract all matched substrings
        result = pattern.findall(input_string)

        return result

    # Example usage:
    input_string = "hello world i am 'Tom Maier' ok"
    result_list = separate_words_with_quotes(input_string)
    print(result_list)


# print(seperate_string())
def pydanticUNset():
    from pydantic import BaseModel, Field

    class MyClass(BaseModel):
        id: Optional[int] = Field(default="bla")
        name: str = Field()

    myobj = MyClass(name="Hello")
    print(myobj.model_dump(exclude_unset=True))


def dynamic_pageparam_order_by():
    import inspect
    from pydantic import Field, BaseModel
    import fastapi
    from fastapi import Depends, Query
    from typing import Generic, TypeVar, get_args, Annotated
    import uvicorn
    import enum

    app = fastapi.FastAPI()
    M = TypeVar("M")

    class Event(BaseModel):
        id: int
        name: str

    # https://docs.pydantic.dev/latest/concepts/models/#generic-models
    class PaginatedResponse(BaseModel, Generic[M]):
        total_count: Optional[int] = Field(
            default=None,
            description="Total number of items in the database",
            examples=[300],
        )
        offset: int = Field(
            description="Starting position index of the returned items in the dataset.",
            examples=[299],
        )
        count: int = Field(
            description="Number of items returned in the response", examples=[1]
        )
        items: List[M] = Field(
            description="List of items returned in the response following given criteria"
        )

    class MetaQueryParamsChangeTypeHintsForOrderBy(type):

        def __new__(cls, name, bases, attr):
            if attr["__orig_bases__"][0] != Generic[M]:
                target_model_attributes = list(
                    get_args(attr["__orig_bases__"][0])[0].model_fields.keys()
                )
                print("name", name)
                print("attr", attr)
                print(
                    "bases",
                )
                new_typing_with_literals = Literal[tuple(target_model_attributes)]

                print("new_literals", new_typing_with_literals)
                print(
                    'bases[0].__init__.__annotations__["order_by"]',
                    bases[0].__init__.__annotations__["order_by"],
                )
                bases[0].__init__.__annotations__["order_by"] = new_typing_with_literals
                print(
                    "__init__",
                    list(inspect.signature(bases[0].__init__).parameters.items())[1:],
                )
                for index, init_param_name in enumerate(
                    list(inspect.signature(bases[0].__init__).parameters.keys())[1:]
                ):
                    print("index", index)
                    print("init_param_name", init_param_name)
                    print(
                        "bases[0].__init__.__defaults__[index]",
                        bases[0].__init__.__defaults__[index],
                    )
                    if init_param_name in attr["defaults"]:
                        print("SET ", init_param_name, "TO ", attr["defaults"])
                        new_defaults = list(bases[0].__init__.__defaults__)
                        new_defaults[index] = attr["defaults"][init_param_name]
                        bases[0].__init__.__defaults__ = tuple(new_defaults)

                print("default", bases[0].__init__.__defaults__)

            # print(attr["__init__"])
            return super().__new__(cls, name, bases, attr)

    class QueryParams(Generic[M], metaclass=MetaQueryParamsChangeTypeHintsForOrderBy):
        defaults = dict()

        def __init__(
            self,
            q: str | None = None,
            skip: Annotated[int, Field(description="This is text")] = 0,
            limit: int = 100,
            order_by: Optional[Literal["Generic", "Placeholder"]] = None,
        ):
            self.q = q
            self.skip = skip
            self.limit = limit
            self.order_by = order_by

    class EventQueryParams(QueryParams[Event]):
        defaults = {"limit": 50}

    @app.get(
        "/event2",
        response_model=PaginatedResponse[Event],
        description=f"List all events.",
    )
    def list_events2(
        query: Annotated[EventQueryParams, Depends(EventQueryParams)],
    ) -> PaginatedResponse[Event]:
        return PaginatedResponse(
            total_count=events,
            offset=query.offset,
            count=len(events),
            items=events[query.offset, query.limit],
        )

    uvicorn.run(
        app,
        host="localhost",
        port=8888,
    )


def GenericTyping():
    from typing import Generic, Literal, TypeVar, get_type_hints, get_args
    from pydantic import BaseModel

    M = TypeVar("M")

    class MetaQueryParamsChangeTypeHinterForOrderBy(type):

        def __new__(cls, name, bases, attr):
            if attr["__orig_bases__"][0] != Generic[M]:
                event_attributes = list(
                    get_args(attr["__orig_bases__"][0])[0].model_fields.keys()
                )
                print("name", name)
                print("attr", attr)
                print(
                    "bases",
                )
                bases[0].__init__.__annotations__["order_by"].__dict__["__args__"] = (
                    tuple(event_attributes)
                )

                print(
                    "Event keys",
                    list(get_args(attr["__orig_bases__"][0])[0].model_fields.keys()),
                )

            # print(attr["__init__"])
            return super().__new__(cls, name, bases, attr)

    class QueryParams(Generic[M], metaclass=MetaQueryParamsChangeTypeHinterForOrderBy):

        def __init__(
            self,
            items: List[M],
            order_by: Optional[Literal["Generics", "Placeholder"]] = None,
        ):
            # print(get_type_hints(self.__class__.__init__)["items"])
            actual_type = tuple(self.__orig_bases__[0].__args__[0].model_fields.keys())
            # print(actual_type)
            self.items = items
            self.order_by = order_by

    class Event(BaseModel):
        id: int
        name: str

    class EventQueryParams(QueryParams[Event]):
        pass

    q = EventQueryParams([Event(id=1, name="A"), Event(id=2, name="B")], "id")

    print(get_type_hints(EventQueryParams.__init__))


def get_enum_by_str():
    from enum import Enum

    class MyEnum(str, Enum):
        ONE = 1
        TWO = 2

    val = "ONE"
    print(MyEnum[val].value)


def get_class_attr_as_str():
    from pydantic import BaseModel

    class Event(BaseModel):
        order_pos: str

    attr_name = Event.order_pos
    print(type(attr_name), attr_name)
    # does not work :(


def nested_pydnatic_val():
    from pydantic import Field
    from pydantic_settings import BaseSettings

    class Config(BaseSettings):
        APP_NAME: str = "DZD MedLog"
        FRONTEND_FILES_DIR: str = Field(
            description="The generated nuxt dir that contains index.html,...",
            default="MedLog/frontend/.output/public",
        )
        FRONTED_FILE: str = Field(
            description="The generated nuxt dir that contains index.html,...",
            default=FRONTEND_FILES_DIR,
        )

    print(Config())


def path_test():
    from pathlib import Path

    print(Path(Path(__file__).parent, "default.yaml"))


def pydnatic_shadow_warning_test():
    # /usr/local/lib/python3.11/site-packages/pydantic/_internal/_fields.py:201: UserWarning: Field name "created_at" in "EventExport" shadows an attribute in parent "Event"
    from sqlmodel import SQLModel, Field

    # from pydantic import BaseModel, Field
    import datetime

    class Event(SQLModel, table=True):
        name: str = Field(primary_key=True)
        created_at: datetime.datetime = Field()

    class EventExport(Event, table=False):
        created_at: datetime.datetime = Field(exclude=True)


def dynamic_pclass_test():
    from pydantic import create_model, Field

    create_model("fuck", arsch=(str, Field(default=None)))


def named_tuple_test():
    from typing import NamedTuple

    class my(NamedTuple):
        val: str
        key: str

    a = my("A", "a")._asdict()
    print(a)


def named_tuple_as_db_col():
    from typing import NamedTuple
    import uuid

    from pydantic import PositiveInt
    from sqlmodel import Field, SQLModel, create_engine, Session, select, Column, JSON

    engine = create_engine(url="sqlite:///./testdb.sqlite")

    class Coordinates(NamedTuple):
        latitude: float
        longitude: float
        altitude: float

    class Address(SQLModel, table=True):
        id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
        zipcode: PositiveInt
        coordinates: Coordinates = Field(sa_column=Column(JSON))

    SQLModel.metadata.create_all(engine)
    coordinates = Coordinates(1.2, 1.3, 1.4)
    coordinates_from_db = None

    # Lets write an address with our NamedTuple coordinates into the DB
    with Session(engine) as s:
        s.add(Address(zipcode="55252", coordinates=Coordinates(1.2, 1.3, 1.4)))
        s.commit()

    # And now lets it read it from the DB
    with Session(engine) as s:
        adr = s.exec(select(Address)).first()
        coordinates_from_db = adr.coordinates

    # Now we compare our NamedTuple coordinates with the stuff that came from the DB
    print("FROM MEM", type(coordinates), coordinates)
    # > FROM MEM <class '__main__.named_tuple_as_db_col.<locals>.Coordinates'> Coordinates(latitude=1.2, longitude=1.3, altitude=1.4)
    print("FROM DB", type(coordinates_from_db), coordinates_from_db)
    # > FROM DB <class 'list'> [1.2, 1.3, 1.4]
    print("Is it the same?", coordinates == coordinates_from_db)
    # > False
    print(
        "is it the same if cast the result back into coordinates?",
        Coordinates(*coordinates_from_db) == coordinates,
    )
    # > True
    # Yay!

    # Although the type of `coordinates_from_db` is a `list` we use it to write coordinates into the databse
    with Session(engine) as s:
        # This works!
        s.add(Address(zipcode="55253", coordinates=coordinates_from_db))
        s.commit()


def str_enum_test():
    from typing import Callable
    import enum
    from functools import partial
    import datetime

    from dataclasses import dataclass

    @dataclass
    class TypCastingInfo:
        python_type: Callable
        casting_func: Callable

    # We need an string Enum here. This is a fixed constraint
    class MyEnum(enum.Enum):
        state1 = TypCastingInfo(int, int)

    val = MyEnum.state1.value
    print(val)
    print(type(val))
    exit()
    print(
        MyEnum.state1.value
    )  # returns `str_enum_test.<locals>.TypCastingInfo(python_type=<class 'int'>, casting_func=<class 'int'>)`

    print(
        type(MyEnum.state1._value_)
    )  # returns `<class 'str'>` instead of `<class 'TypCastingInfo'>`. Why?

    print(
        MyEnum.state1._value_.python_type
    )  # This is not possible and throws and error `AttributeError: 'str' object has no attribute 'python_type'`


def classnametest():
    class MyClass:
        def __init__(self):
            pass

        def printname(self):
            print(self.__class__.__name__)

    my = MyClass()
    my.printname()


def python_typing_unpack():
    from typing_extensions import Unpack

    # that seems to be a wrong usage(arrocding to chatgpt. investiuagte further)
    def myfunc(**kwargs: Unpack[int | str]):
        print(bool(kwargs))

    myfunc(d="")


def python_typing_unpack2():
    from typing_extensions import TypedDict, Unpack

    class Person(TypedDict):
        name: str
        age: int

    def greet_person(**kwargs: Unpack[Person]) -> None:
        print(f"Hello, {kwargs['name']}! You are {kwargs['age']} years old.")

    # Using unpacked keyword arguments from the TypedDict
    greet_person(name="Alice", age=30)  # This works


def enum_as_dict_keys():
    import enum
    from pydantic import BaseModel

    class Things(enum.Enum):
        books = "books"
        shoes = "shoes"

    d = dict()
    d[Things.books.name] = "Was ist was Band 1"
    d[Things.shoes] = "Sneakers"

    print(d)


def extract_sb_value():
    import re

    def extract_bracket_values(input_string, count, default=None) -> list[str]:

        # Find all occurrences of values inside square brackets
        matches = re.findall(r"\[([^\]]+)\]", input_string)

        # Check if we have enough matches
        if len(matches) < count:
            if default is not None:
                # If not enough matches, extend with default value
                matches.extend([default] * (count - len(matches)))
            else:
                # Raise an error if there are not enough matches and no default value
                raise ValueError(
                    f"Expected {count} values, but only found {len(matches)}."
                )

        # Return the first `count` values as a tuple
        return tuple(matches[:count])

    # e.g. ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]
    # we need the first key for now. e.g. "PACKAGEID"
    # Use regular expression to find the first occurrence of a value inside the square brackets
    print(
        extract_bracket_values(
            "ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]", 1
        )
    )
    print(
        extract_bracket_values(
            "ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]",
            4,
            default="bla",
        )
    )
    print(
        extract_bracket_values(
            "ARV_PACKAGEGROUP.CSV[PACKAGEID]/PACKAGE.CSV[ID]>[PRODUCTID]",
            4,
        )
    )


def sqlmodel_emtpy_val():
    import uuid
    from sqlmodel import SQLModel, Field

    class DrugVal(SQLModel, table=True):
        __tablename__ = "drug_attr_val"

        drug_id: uuid.UUID = Field(foreign_key="drug.id", primary_key=True)
        field_name: str = Field(
            primary_key=True, foreign_key="drug_attr_field_definition.field_name"
        )
        value: Optional[str] = Field(
            default=None,
            description="Generic storage of a value as string. Can be typed via the function in DrugAttrFieldDefinition.type",
        )

    d = DrugVal(field_name="Bla", value="1")
    d2 = DrugVal()
    d2.value = "Bla"
    print(d)
    print(d2)


def nested_sqlmodel_obj_commit():
    from pathlib import Path
    from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship

    class Parent(SQLModel, table=True):
        name: str = Field(primary_key=True)
        children: List["Child"] = Relationship(back_populates="parent")

    class Child(SQLModel, table=True):
        name: str = Field(primary_key=True)
        parent_id: str = Field(foreign_key="parent.name")
        parent: Parent = Relationship(back_populates="children")

    dbpath = Path("/tmp/database.db")
    dbpath.unlink(missing_ok=True)
    sqlite_url = f"sqlite:///{dbpath}"

    engine = create_engine(sqlite_url, echo=False)

    def create_db_and_tables():
        SQLModel.metadata.create_all(engine)

    p = Parent(name="Freddy")
    c = Child(name="Frederike")
    p.children.append(c)
    create_db_and_tables()
    with Session(engine) as session:
        session.add(p)
        session.commit()
    with Session(engine) as session:
        res = session.exec(select(Parent))
        print(res.one().children)


def sqlite_path():
    import os
    from urllib.parse import urlparse
    from pathlib import Path

    def get_sqlite_path(db_url: str) -> Path:
        """
        Checks if the given SQL connection URL points to a SQLite file.
        If so, creates any missing parent directories for the file path and returns the path

        Parameters:
            db_url (str): The SQL database connection URL.

        Returns:
            Path | None: Path instance if it was a SQLite file and directories were ensured/created,
                None if not a SQLite file.
        """
        parsed_db_url = urlparse(db_url)

        # SQLite URLs typically look like: sqlite:///path/to/db.sqlite3
        if "sqlite" not in parsed_db_url.scheme:
            return None
        # remove sqlite style leading "/" (see https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#connect-strings)
        db_path_clean = parsed_db_url.path[1:]
        if db_path_clean == ":memory:":
            # Skip in-memory SQLite
            return None
        full_db_path = Path(db_path_clean).resolve()
        # full_db_path.parent.mkdir(exist_ok=True, parents=True)
        return full_db_path

    print(
        "sqlite:////absolute/path/to/my.sqlite",
        get_sqlite_path("sqlite:////absolute/path/to/my.sqlite"),
    )
    print(
        "sqlite+aiosqlite:///dbs/test.sqlite",
        get_sqlite_path("sqlite+aiosqlite:///dbs/test.sqlite"),
    )
    print("sqlite:///./local.sqlite", get_sqlite_path("sqlite:///./local.sqlite"))


import datetime
import random


def random_past_date(
    min_date: datetime.date, random_gen: random.Random = None
) -> datetime.date:
    """
    Generate a random date between a minimum date (default: two years ago) and today.

    Args:
        min_date (date, optional): The earliest allowable date. Defaults to two years ago from today.

    Returns:
        date: A random date between min_date and today.
    """
    today = datetime.date.today()
    if random_gen is None:
        random_gen = random.Random()
    if min_date is None:
        min_date = today - datetime.timedelta(days=730)  # Approx. 2 years
    if min_date > today:
        raise ValueError("min_date cannot be in the future.")

    delta_days = (today - min_date).days
    random_days = random_gen.randint(0, delta_days)
    return min_date + datetime.timedelta(days=random_days)


print(random_past_date())
