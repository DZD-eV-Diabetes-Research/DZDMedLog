from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn

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
    Response,
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

from medlogserver.db.event.event import Event, EventUpdate, EventCRUD, get_event_crud


from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)
from medlogserver.config import Config
from medlogserver.db.interview.interview import (
    Interview,
    InterviewCreate,
    InterviewCRUD,
    InterviewUpdate,
    get_interview_crud,
)
from medlogserver.REST_api.routes_app.security import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    UserStudyAccessCollection,
)

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_interview_router: APIRouter = APIRouter()


@fast_api_interview_router.get(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of an event.",
)
async def list_interviews(
    event_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Interview]:
    return await interview_crud.list(filter_by_event_id=event_id)


@fast_api_interview_router.get(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    response_model=Interview,
    description=f"Get a certain interview by its id.",
)
async def get_interview(
    event_id: Annotated[str, Path()],
    interview_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Interview]:
    interview = await interview_crud.get(interview_id=interview_id)
    if interview.event_id == event_id:
        return interview
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview with this id under this event available",
        )


@fast_api_interview_router.post(
    "/study/{study_id}/event/{event_id}/interview",
    response_model=List[Interview],
    description=f"Create new interview",
)
async def create_interview(
    interview: Annotated[InterviewCreate, Body()],
    event_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> User:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
        )
    return await interview_crud.create(interview)


@fast_api_interview_router.patch(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    response_model=Interview,
    description=f"Update existing interview",
)
async def update_interview(
    interview_id: str,
    event_id: str,
    interview_update: InterviewUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> User:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            details="User not authorized to create interview in this study",
        )
    interview_from_db = await interview_crud.get(interview_id)
    if interview_from_db is None or interview_from_db.event_id != event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No interview with this id under this event available",
        )
    return await interview_crud.update(interview_id, interview_update)


@fast_api_interview_router.delete(
    "/study/{study_id}/event/{event_id}/interview/{interview_id}",
    description=f"Delete existing interview - Not Yet Implented",
    response_class=Response,
    status_code=204,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": None},
    },
)
async def delete_interview(
    interview_id: str,
    event_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> None:
    if not study_access.user_has_interviewer_permission():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized to update event",
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deleting a event is not implented",
    )
    # not implemented. Do we need that?
    # That would be a whole process -> delete interviews, intakes. More something for a background task.
    # "a mark for deletion" property and a grace period of one day. or an validation by email  would make sense to prevent accidentaly deletion.
    # or a disable option
    return await event_crud.delete(
        event_id=event_id,
        raise_exception_if_not_exists=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No event with id '{event_id}'",
        ),
    )


@fast_api_interview_router.get(
    "/study/{study_id}/proband/{proband_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of one proband.",
)
async def list_interviews_of_proband(
    proband_id: Annotated[str, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Interview]:
    return await interview_crud.list(filter_by_proband_external_id=proband_id)


@fast_api_interview_router.get(
    "/study/{study_id}/interview",
    response_model=List[Interview],
    description=f"List all interviews of one study.",
)
async def list_all_study_interviews(
    study_access: UserStudyAccess = Security(user_has_study_access),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Interview]:
    return await interview_crud.list(filter_by_study_id=study_access.study.id)
