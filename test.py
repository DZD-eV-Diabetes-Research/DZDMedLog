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


test_pzn_cleaner()
