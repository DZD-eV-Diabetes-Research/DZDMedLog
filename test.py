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
    from pydantic import Field, BaseModel
    import fastapi
    from fastapi import Depends, Query
    from typing import Generic, TypeVar, get_type_hints, Annotated
    import uvicorn

    app = fastapi.FastAPI()
    M = TypeVar("M")

    class PageParams(BaseModel, Generic[M]):

        offset: int = Field(
            default=0,
            description="Starting position index of the returned items in the dataset.",
            examples=[200],
        )
        limit: Optional[int] = Field(
            default=100,
            description="Max number if items to be included in the response.",
            examples=[50],
        )
        """
        order_by: Literal[
            tuple(get_type_hints(M).keys() if isinstance(M, BaseModel) else "Generic")
        ] = Field(
            default=None, description="The attribute name to order the results by"
        )
        """
        order_by: Literal["ABC", "DEF"] = Field()

        order_desc: Optional[bool] = Field(
            default=False,
            description="If set to True order descending otherwise order result ascending",
        )

        def append_to_query(self, q, no_limit: bool = True):
            q = q.offset(self.offset)
            if self.limit and not no_limit:
                q = q.limit(self.limit)
            return q

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

    def pagination_query(
        offset: int = 0,
        limit: int = Query(default=100, le=1000),
        order_by: str = None,
        order_desc: bool = False,
    ) -> PageParams:
        """Function to be included as a "Depends" in a FastAPi route.

        Args:
            offset (int, optional): _description_. Defaults to 0.
            limit (int, optional): _description_. Defaults to Query(default=100, le=1000).
            order_by (str, optional): _description_. Defaults to None.
            order_desc (bool, optional): _description_. Defaults to False.

        Returns:
            PageParams: _description_
        """
        return PageParams(
            offset=offset, limit=limit, order_by=order_by, order_desc=order_desc
        )

    class Event(BaseModel):
        id: int
        name: str
        description: Optional[str] = None

    events: List[Event] = [
        Event(id=1, name="Party"),
        Event(id=2, name="Sleep"),
        Event(id=3, name="Dinner"),
    ]

    @app.get(
        "/event",
        response_model=PaginatedResponse[Event],
        description=f"List all events.",
    )
    def list_events(
        pagination: PageParams[Event] = Depends(pagination_query),
    ) -> PaginatedResponse[Event]:
        return PaginatedResponse(
            total_count=events,
            offset=pagination.offset,
            count=len(events),
            items=events[pagination.offset, pagination.limit],
        )

    class QueryParams(Generic[M]):

        def __init__(
            self,
            q: str | None = None,
            skip: int = 0,
            limit: int = 100,
            order_by: Literal[
                tuple(
                    m.model_fields() if M.__name__ == BaseModel else ["Generic", "FUCK"]
                )
            ] = None,
        ):
            print("M.__name__", M.__name__)
            self.q = q
            self.skip = skip
            self.limit = limit
            self.order_by = order_by

    @app.get(
        "/event2",
        response_model=PaginatedResponse[Event],
        description=f"List all events.",
    )
    def list_events2(
        query: Annotated[QueryParams[Event], Depends(QueryParams)],
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
    from typing import Generic, Literal, TypeVar, get_type_hints
    from pydantic import BaseModel

    M = TypeVar("M")

    class MetaQueryParamsChangeTypeHinterForOrderBy(type):

        def __new__(cls, name, bases, attr):
            print("attr.__orig_bases__[0]", "__orig_bases__"][0])

            # print(attr["__init__"])
            return super().__new__(cls, name, bases, attr)

    class QueryParams(Generic[M], metaclass=MetaQueryParamsChangeTypeHinterForOrderBy):

        def __init__(
            self,
            items: List[M],
            order_by: Literal["Generics", "Placeholder"] = None,
        ):
            print(get_type_hints(self.__class__.__init__)["items"])
            actual_type = tuple(self.__orig_bases__[0].__args__[0].model_fields.keys())
            print(actual_type)
            self.items = items
            self.order_by = order_by

        def fuck(self):
            pass

    class Event(BaseModel):
        id: int
        name: str

    class EventQueryParams(QueryParams[Event]):
        pass

    q = EventQueryParams([Event(id=1, name="A"), Event(id=2, name="B")], "id")

    print(get_type_hints(EventQueryParams.__init__))


GenericTyping()
"""
    class QueryParams(Generic[M]):

        def __init__(
            self,
            items: List[M],
            order_by: Literal[
                tuple(
                    m.model_fields
                    if M.__name__ == BaseModel
                    else ("Generics", "Placeholder")
                )
            ] = None,
        ):
            print("M.__name__", M.__name__)
            self.items = items
            self.order_by = order_by
"""
