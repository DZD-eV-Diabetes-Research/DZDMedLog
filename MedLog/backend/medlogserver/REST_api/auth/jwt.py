from pydantic import BaseModel, Field
from uuid import UUID

from datetime import datetime, timedelta, timezone
from typing import List, Literal
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import HTTPException, status

#
from medlogserver.config import Config
from medlogserver.log import get_logger

log = get_logger()
config = Config()


class JWTTokenResponse(BaseModel):
    token: str = Field(
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
        description="JWT token to be used to authenticate against the API",
    )
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(
        description="The number of seconds until the token expires", examples=[3600]
    )


class JWTTokenContainer:
    def __init__(
        self,
        sub: str,
        user_name: str,
        user_groups: List[str] = None,
        scope: List[str] = None,
        prevent_generate_new_token: bool = False,
    ):
        """_summary_

        Args:
            sub (str): "Subject" - the user name/id
            scope (List[str], optional): _description_. Defaults to None.
            prevent_generate_new_token (bool, optional): _description_. Defaults to False.
        """
        if scope is None:
            scope = []
        self.scope: List[str] = scope
        self.sub: str = sub
        self.name: str = user_name
        self.grps: List[str] = user_groups
        self.exp: datetime = None
        self.jwt_token: str = None
        self.id: UUID = None
        if not prevent_generate_new_token:
            self._generate_token()

    @property
    def user_id(self) -> str:
        # alias for sub. sub is the standard name for the user identifier in JWT but user_id more descriptive in a python context
        return self.sub

    @property
    def user_name(self) -> str:
        # alias for name. we want short attributes names in a jwt context to get a compact payload but more descriptive in a python context
        return self.name

    @property
    def user_groups(self) -> str:
        # alias for grps. we want short attributes names in a jwt context to get a compact payload but more descriptive in a python context
        return self.grps

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.exp

    def get_response(self) -> JWTTokenResponse:
        return JWTTokenResponse(
            token=self.jwt_token,
            token_type="Bearer",
            expires_in=int((self.exp - datetime.now(timezone.utc)).total_seconds()),
        )

    def _generate_token(self):
        expire_moment: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=config.AUTH_ACCESS_TOKEN_EXPIRES_MINUTES
        )
        self.exp = expire_moment
        self.jwt_token = jwt.encode(
            claims={
                "sub": self.sub,
                "exp": self.exp.timestamp(),
                "aud": str(config.get_server_url()),
                "scope": " ".join(self.scope),
                "iss": config.SERVER_HOSTNAME,
                "name": self.name,
                "grps": " ".join(self.grps),
                "id": str(self.id),
            },
            key=config.AUTH_JWT_SECRET,
            algorithm=config.AUTH_JWT_ALGORITHM,
        )

    @classmethod
    def from_existing_encoded_jwt(cls, jwt_token: str) -> Self:
        try:
            jwt_token_decoded = jwt.decode(
                jwt_token, config.AUTH_JWT_SECRET, config.AUTH_JWT_ALGORITHM
            )
            new_obj = cls(
                sub=jwt_token_decoded["sub"],
                user_name=jwt_token_decoded["name"],
                user_groups=jwt_token_decoded["grps"].split(" "),
                scope=jwt_token_decoded["scope"].split(" "),
                prevent_generate_new_token=True,
            )
            new_obj.jwt_token = jwt_token
            new_obj.id = UUID(jwt_token_decoded["id"])
            new_obj.exp = datetime.fromtimestamp(jwt_token_decoded["exp"])
            return new_obj
        except JWTError as exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supplied authentication could not be validated ({exp})",
            )
