from pydantic import BaseModel, Field
from uuid import UUID

from datetime import datetime, timedelta, timezone
from typing import List, Literal, Dict
from typing_extensions import Self
from jose import JWTError, jwt
from fastapi import HTTPException, status
import json

#
from medlogserver.db.user import User
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
    expires_in_sec: int = Field(
        description="The number of seconds until the token expires", examples=[3600]
    )
    expires_at_utc: float = Field()


class JWTTokenContainer:
    def __init__(
        self,
        user: User,
        prevent_generate_new_token: bool = False,
    ):
        """_summary_

        Args:
            user (User): _description_
            prevent_generate_new_token (bool, optional): _description_. Defaults to False.
        """
        self.scope: List[str] = user.roles
        self.sub: str = user.username
        self.exp_datetime: datetime = None

        self.jwt_token_encoded: str = None
        self.user: User = user
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

    @property
    def exp(self) -> int:
        """Expiration time for the jwt token as Posix timestamp as its defined in https://www.rfc-editor.org/rfc/rfc7519#section-4.1.4
        Returns:
            int: Posix timestamp
        """
        return int(self.exp_datetime.timestamp())

    def get_response(self) -> JWTTokenResponse:
        return JWTTokenResponse(
            token=self.jwt_token_encoded,
            token_type="Bearer",
            expires_in_sec=int(self.exp - datetime.now(timezone.utc).timestamp()),
            expires_at_utc=int(self.exp),
        )

    @property
    def jwt_token_decoded(self) -> Dict:
        return jwt.decode(
            self.jwt_token_encoded, config.AUTH_JWT_SECRET, config.AUTH_JWT_ALGORITHM
        )

    def _generate_token(self):
        self.exp_datetime: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=config.AUTH_ACCESS_TOKEN_EXPIRES_MINUTES
        )
        self.jwt_token_encoded = jwt.encode(
            claims={
                "sub": self.sub,
                "exp": self.exp,
                "aud": str(config.get_server_url()),
                "scope": " ".join(self.scope),
                "iss": config.SERVER_HOSTNAME,
                # Dumping the whole user object in the token, is a very heavy payload and maybe a bad idea.
                # lets analize later if database access to load the user object (and just save the user id here) every request is maybe better perfoming.
                # (Which would defeat the whole purpose of jwt tokens :D. then we could switch to good old opaque tokens)
                # TODO: do some tests and thinking here before deciding
                "user": self.user.model_dump_json(),
                "id": str(self.id),
            },
            key=config.AUTH_JWT_SECRET,
            algorithm=config.AUTH_JWT_ALGORITHM,
        )

    @classmethod
    def from_existing_jwt(cls, jwt_token_encoded: str) -> Self:
        try:
            jwt_token_decoded = jwt.decode(
                jwt_token_encoded, config.AUTH_JWT_SECRET, config.AUTH_JWT_ALGORITHM
            )
            new_obj = cls(
                # sub=jwt_token_decoded["sub"],
                # scope=jwt_token_decoded["scope"].split(" "),
                user=User(**json.load(jwt_token_decoded["user"])),
                prevent_generate_new_token=True,
            )
            new_obj.jwt_token_encoded = jwt_token_encoded
            new_obj.id = UUID(jwt_token_decoded["id"])
            new_obj.exp_datetime = datetime.fromtimestamp(jwt_token_decoded["exp"])
            return new_obj
        except JWTError as exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supplied authentication could not be validated ({exp})",
            )
