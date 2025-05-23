from typing import AsyncGenerator, List, Optional, Literal, Sequence, Annotated
from pydantic import BaseModel, Field


from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()


# Only for the /role metadata endpoint. This is not an existing object in the database.
# roles only exists as a list of strings in the "User"-model
class UserRoleApiRead(BaseModel):
    role_name: str = Field(
        description="The name and identifier of the rule. It can be applied to user objects."
    )
    description: Optional[str] = Field(
        default="", description="Description of the role."
    )
