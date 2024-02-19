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

from medlogserver.api.auth.tokens import (
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
from medlogserver.api.auth.base import (
    TOKEN_ENDPOINT_PATH,
    oauth2_scheme,
    user_is_admin,
    user_is_usermanager,
    get_current_user,
    NEEDS_ADMIN_API_INFO,
    NEEDS_USERMAN_API_INFO,
)
from medlogserver.api.routes_app.security import (
    get_current_user,
)
from medlogserver.db.event.model import Event, EventUpdate
from medlogserver.db.event.crud import EventCRUD, get_event_crud

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
    UserAuthExternalOIDCTokenCRUD,
    get_user_auth_external_oidc_token_crud,
)
from medlogserver.config import Config
from medlogserver.db.wido_gkv_arzneimittelindex.model import Stamm, StammRead
from medlogserver.db.wido_gkv_arzneimittelindex.crud import StammCRUD, get_stamm_crud

from medlogserver.api.base import HTTPMessage
from medlogserver.api.paginator import pagination_query, PageParams, PaginatedResponse

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_drug_router: APIRouter = APIRouter()


#############
@fast_api_drug_router.get(
    "/drug",
    # response_model=PaginatedResponse[Stamm],
    response_model=List[StammRead],
    description=f"List medicine/drugs from the system",
)
async def list_all_intakes_of_last_completed_interview(
    user: User = Security(get_current_user),
    pagination: PageParams = Depends(pagination_query),
    drug_stamm_crud: StammCRUD = Depends(get_stamm_crud),
) -> List[StammRead]:
    result_items = await drug_stamm_crud.list(pagination=pagination)
    return result_items
    return PaginatedResponse(
        total_count=await drug_stamm_crud.count(),
        offset=pagination.offset,
        count=len(result_items),
        items=result_items,
    )
    # return await drug_stamm_crud.list()


"""
############
@fast_api_drug_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands last completed interview.",
)
async def list_all_intakes_of_last_uncompleted_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Intake]:
    last_uncompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if last_uncompleted_interview:
        return await intake_crud.list(
            filter_by_interview_id=last_uncompleted_interview.id
        )
    else:
        return []


############
@fast_api_drug_router.get(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of interview.",
)
async def list_all_intakes_of_interview(
    interview_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Intake]:

    return await intake_crud.list(
        filter_by_interview_id=interview_id, filter_by_study_id=study_access.study.id
    )


############
@fast_api_drug_router.get(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description=f"Get a certain intake record by it id",
)
async def get_intake(
    intake_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
) -> Intake:
    return await intake_crud.get(
        intake_id=intake_id,
        study_id=study_access.study.id,
        raise_exception_if_none=HTTPException(status_code=status.HTTP_404_NOT_FOUND),
    )


############
@fast_api_drug_router.post(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"Create intake record in certain interview. user must have at least 'interviewer'-permissions on study.",
)
async def create_intake(
    interview_id: str,
    intake: IntakeCreate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of the study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    intake.interview_id == interview_id
    return await intake_crud.create(intake)


############
@fast_api_drug_router.patch(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=List[Intake],
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def update_intake(
    interview_id: str,
    intake_id: str,
    intake: IntakeUpdate,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    intake.interview_id == interview_id
    return await intake_crud.update(intake_id, intake)


############
@fast_api_drug_router.delete(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=List[Intake],
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def delete_intake(
    interview_id: str,
    intake_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(get_intake_crud),
    interview_crud: InterviewCRUD = Depends(get_interview_crud),
) -> List[Intake]:
    if not study_access.user_has_interviewer_permission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    assert await assert_interview_id_is_part_of_study_id(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    log.warning("ToDo: The med record are not deleted yet")
    return await intake_crud.delete(intake_id)
"""
