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


pydanticUNset()
