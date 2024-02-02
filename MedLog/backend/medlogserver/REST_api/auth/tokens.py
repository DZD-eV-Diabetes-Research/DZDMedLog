from pydantic import BaseModel, Field
from uuid import UUID, uuid4

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


class JWTTokenResponseBase(BaseModel):
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = Field(
        description="The number of seconds until the token expires", examples=[3600]
    )
    expires_at: int = Field(
        description="The time as POSIX timestamp in UTC when the token expires",
        examples=[int((datetime.now().timestamp() + 3600))],
    )


class JWTAccessTokenResponse(JWTTokenResponseBase):
    access_token: str = Field(
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
        description="Token to be used to authenticate against the API",
    )


class JWTRefreshTokenResponse(JWTTokenResponseBase):
    refresh_token: str = Field(
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
        description="Refresh token to be used to get new access tokens",
    )


class JWTBundleTokenResponse(JWTAccessTokenResponse, JWTRefreshTokenResponse):
    refresh_token_expires_in: int = Field(
        description="The number of seconds until the token expires", examples=[3600]
    )
    refresh_token_expires_at: int = Field()


class JWTRefreshTokenContainer:
    def __init__(
        self,
        user_id: UUID,
        prevent_generate_new_token: bool = False,
    ):
        self.user_id: UUID = user_id
        self.id: UUID = None
        self.created_at: datetime = None
        if not prevent_generate_new_token:
            self._generate_token()

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(
            minutes=config.AUTH_REFRESH_TOKEN_EXPIRES_MINUTES
        )

    @property
    def exp(self):
        return int(self.expires_at.timestamp())

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def _generate_token(self):
        self.created_at = datetime.now(timezone.utc) + timedelta(
            minutes=config.AUTH_REFRESH_TOKEN_EXPIRES_MINUTES
        )
        if self.id is None:
            self.id = uuid4()
        self.jwt_token_encoded = jwt.encode(
            claims={
                "sub": str(self.user_id),
                "exp": self.exp,
                "aud": str(config.get_server_url()),
                "iss": config.SERVER_HOSTNAME,
                "id": str(self.id if self.id else uuid4()),
                "iat": self.created_at.timestamp(),
            },
            key=config.AUTH_JWT_SECRET,
            algorithm=config.AUTH_JWT_ALGORITHM,
        )

    @classmethod
    def from_existing_jwt(cls, jwt_token_encoded: str) -> Self:
        try:
            jwt_token_decoded = jwt.decode(
                jwt_token_encoded,
                config.AUTH_JWT_SECRET,
                config.AUTH_JWT_ALGORITHM,
                audience=config.get_server_url().host,
            )

            new_obj = cls(
                user_id=jwt_token_decoded["sub"],
                prevent_generate_new_token=True,
            )
            new_obj.id = UUID(jwt_token_encoded["id"])
            new_obj.jwt_token_encoded = jwt_token_encoded
            new_obj.created_at = datetime.fromtimestamp(
                jwt_token_decoded["iat"], tz=timezone.utc
            )
            return new_obj
        except JWTError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supplied authentication could not be validated ({error})",
            )

    def to_token_response(self) -> JWTRefreshTokenResponse:
        return JWTRefreshTokenResponse(
            refresh_token=self.jwt_token_encoded,
            expires_in=int(self.exp - datetime.now(timezone.utc).timestamp()),
            expires_at_utc=int(self.exp),
        )

    def to_token_set_response(
        self, access_token: "JWTAccessTokenContainer"
    ) -> JWTBundleTokenResponse:
        """A token json bundle/set containing a refresh and a access token. usally issued after a new login.

        Args:
            access_token (JWTAccessTokenContainer): An existiung access token that will be bundled with the refresh token

        Returns:
            JWTBundleTokenResponse: A fastapi ready response containing the tokens
        """
        return JWTBundleTokenResponse(
            refresh_token=self.jwt_token_encoded,
            access_token=access_token.jwt_token_encoded,
            expires_in=int(access_token.exp - datetime.now(timezone.utc).timestamp()),
            expires_at=int(access_token.exp),
            refresh_token_expires_in=int(
                self.exp - datetime.now(timezone.utc).timestamp()
            ),
            refresh_token_expires_at=int(self.exp),
        )


class JWTAccessTokenContainer:
    def __init__(
        self,
        user: User,
        parent_refresh_token_id: UUID = None,
        prevent_generate_new_token: bool = False,
    ):
        """_summary_

        Args:
            user (User): _description_
            prevent_generate_new_token (bool, optional): _description_. Defaults to False.
        """
        self.sub: str = user.id
        self.user: User = user
        self.id: UUID = None
        self.created_at = None
        self.jwt_token_encoded: str = None
        self._parent_refresh_token_id: UUID = parent_refresh_token_id
        if not prevent_generate_new_token and parent_refresh_token_id is not None:
            self._generate_token()
        elif not prevent_generate_new_token and parent_refresh_token_id is None:
            raise ValueError(
                "Can not generate Access token without specifiing the parent Refresh token id"
            )

    @property
    def user_id(self) -> str:
        # alias for sub. sub is the standard name for the user identifier in JWT but user_id more descriptive in a python context
        return self.sub

    @property
    def user_name(self) -> str:
        # alias for name. we want short attributes names in a jwt context to get a compact payload but more descriptive in a python context
        return self.user.user_name

    @property
    def user_roles(self) -> List[str]:
        # alias for grps. we want short attributes names in a jwt context to get a compact payload but more descriptive in a python context
        return self.user.roles

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(
            minutes=config.AUTH_ACCESS_TOKEN_EXPIRES_MINUTES
        )

    @property
    def exp(self):
        """Expiration time for the jwt token as Posix timestamp as its defined in https://www.rfc-editor.org/rfc/rfc7519#section-4.1.4
        Returns:
            int: Posix timestamp
        """
        return int(self.expires_at.timestamp())

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def to_token_response(self) -> JWTAccessTokenResponse:
        return JWTAccessTokenResponse(
            token=self.jwt_token_encoded,
            token_type="Bearer",
            expires_in=int(self.exp - datetime.now(timezone.utc).timestamp()),
            expires_at=int(self.exp),
        )

    @property
    def jwt_token_decoded(self) -> Dict:
        return jwt.decode(
            self.jwt_token_encoded,
            config.AUTH_JWT_SECRET,
            config.AUTH_JWT_ALGORITHM,
            audience=config.get_server_url().host,
        )

    @property
    def parent_refresh_token_id(self) -> UUID:
        if self._parent_refresh_token_id is None:
            return UUID(self.jwt_token_decoded["refr_id"])
        return self._parent_refresh_token_id

    def _generate_token(self):
        log.info(f"TOKEN AUD: {config.get_server_url().host}")
        self.created_at = datetime.now(timezone.utc)
        self.jwt_token_encoded = jwt.encode(
            claims={
                "sub": str(self.sub),
                "exp": self.exp,
                "iat": int(self.created_at.timestamp()),
                "aud": config.get_server_url().host,
                # "aud": "http://localhost:8888",
                "iss": config.SERVER_HOSTNAME,
                "user": self.user.model_dump_json(),
                "id": str(self.id if self.id else uuid4()),
                "refr_id": str(self._parent_refresh_token_id),
            },
            key=config.AUTH_JWT_SECRET,
            algorithm=config.AUTH_JWT_ALGORITHM,
        )

    @classmethod
    def from_existing_jwt(cls, jwt_token_encoded: str) -> Self:
        try:
            jwt_token_decoded = jwt.decode(
                jwt_token_encoded,
                config.AUTH_JWT_SECRET,
                config.AUTH_JWT_ALGORITHM,
                audience=config.get_server_url().host,
            )
            user = jwt_token_decoded["user"]
            log.debug(f"user ({type(user)}): {user}")
            user_dict: Dict = json.loads(jwt_token_decoded["user"])
            log.debug(f"jwt_token_decoded ({type(user_dict)}): {user_dict}")
            new_obj = cls(
                user=User.model_validate(user_dict),
                prevent_generate_new_token=True,
            )
            new_obj.id = jwt_token_decoded["id"]
            new_obj.jwt_token_encoded = jwt_token_encoded
            new_obj.created_at = datetime.fromtimestamp(
                jwt_token_decoded["iat"], tz=timezone.utc
            )
            return new_obj
        except JWTError as exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Supplied authentication could not be validated ({exp})",
            )
