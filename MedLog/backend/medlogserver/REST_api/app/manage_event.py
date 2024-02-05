from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List

from fastapi import (
    Depends,
    Security,
    FastAPI,
    HTTPException,
    status,
    Query,
    Body,
    Form,
    Path,
)
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from typing import Annotated

from fastapi import Depends, APIRouter

from medlogserver.REST_api.auth.tokens import (
    JWTBundleTokenResponse,
    JWTAccessTokenContainer,
    JWTRefreshTokenContainer,
)
from medlogserver.db.user.user import (
    get_user_crud,
    User,
    UserCRUD,
    UserCreate,
    UserUpdate,
    UserUpdateByUser,
    UserUpdateByAdmin,
)
from medlogserver.db.user.user_auth import (
    get_user_auth_crud,
    UserAuth,
    UserAuthCreate,
    UserAuthUpdate,
    UserAuthCRUD,
    UserAuthRefreshToken,
    UserAuthRefreshTokenCreate,
    UserAuthRefreshTokenCRUD,
    get_user_auth_refresh_token_crud,
    AllowedAuthSourceTypes,
)
from medlogserver.REST_api.auth.base import (
    TOKEN_ENDPOINT_PATH,
    oauth2_scheme,
    user_is_admin,
    user_is_usermanager,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)

from medlogserver.db.event.event import Event, EventCRUD, get_event_crud
from medlogserver.db.study.study_permission import (
    StudyPermisson,
    StudyPermissonCRUD,
    get_study_permission_crud,
)

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)
from medlogserver.config import Config
from medlogserver.REST_api.app.security import (
    user_has_study_access_map,
    UserStudyAccess,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_event_router: APIRouter = APIRouter()


@fast_api_event_router.get(
    "/study/{study_id}/event",
    response_model=List[Event],
    description=f"List all studies the user has access too.",
)
async def get_studies(
    show_deactived: bool = Query(False),
    current_user: User = Security(get_current_user),
    study_permissions_helper: UserStudyAccess = Security(user_has_study_access_map),
    event_crud: EventCRUD = Depends(get_event_crud),
) -> User:

    # ToDo: This is a pretty cost intensive endpoint/query. Would be a good candiate for some kind of cache.
    all_studies = await event_crud.list(show_deactivated=show_deactived)
    allowed_studies: List[Event] = []
    # TODO you are here
    raise NotImplemented()


@fast_api_event_router.post(
    "/study/{study_id}/event",
    response_model=Event,
    description=f"Create a new event. {NEEDS_ADMIN_API_INFO}",
)
async def create_event(
    event: Event,
    current_user_is_admin: User = Security(user_is_admin),
    event_crud: EventCRUD = Depends(get_event_crud),
) -> User:
    return await event_crud.create(
        event,
        raise_exception_if_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event with name '{event.name}' allready exists",
        ),
    )


@fast_api_event_router.patch(
    "/study/{study_id}/event/{event_id}",
    response_model=Event,
    description=f"Update existing event",
)
async def update_event(
    event_id: Annotated[str, Path()],
    event: Annotated[Event, Body(description="The event object with updated data")],
    event_crud: EventCRUD = Depends(get_event_crud),
    current_user: User = Security(get_current_user),
) -> User:
    # security
    not_allowed_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"You are not allowed to update this event",
    )
    passed_security_check: bool = False
    raise NotImplemented


@fast_api_event_router.delete(
    "/study/{study_id}/event/{event_id}",
    description=f"Delete existing event - Not Yet Implented",
)
async def delete_event(
    event_id: Annotated[str, Path()],
    current_user_is_admin: User = Security(user_is_admin),
    event_crud: EventCRUD = Depends(get_event_crud),
) -> User:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deleting a event is not yet implented",
    )
    # not implemented. Do we need that? For a multi event instance propably.
    # That would be a whole process -> delete permissions, events,interviews, intakes. More something for a background task.
    # "a mark for deletion" property and a grace period of one day. or an validation by email  would make sense to prevent accidentaly deletion.
    return await event_crud.delete(event_id=event_id)
