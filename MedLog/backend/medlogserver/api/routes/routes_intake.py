from datetime import datetime, timedelta, timezone
from typing import Annotated, Sequence, List, NoReturn, Type

from fastapi import (
    Depends,
    Security,
    APIRouter,
    HTTPException,
    status,
    Body,
    Path,
    Query,
)
import uuid
from fastapi.responses import JSONResponse
from medlogserver.db.interview import InterviewCRUD
from medlogserver.model.intake import (
    Intake,
    IntakeCreate,
    IntakeUpdate,
    IntakeCreateAPI,
    IntakeDetailListItem,
)
from medlogserver.db.intake import IntakeCRUD
from medlogserver.api.study_access import (
    user_has_studies_access_map,
    user_has_study_access,
    UserStudyAccess,
    assert_interview_is_part_of_study,
    assert_intake_is_part_of_study,
)
from medlogserver.api.paginator import (
    PaginatedResponse,
    create_query_params_class,
    QueryParamsInterface,
)
from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_intake_router: APIRouter = APIRouter()


IntakeQueryParams: Type[QueryParamsInterface] = create_query_params_class(
    Intake, default_order_by_attr="created_at"
)


############
@fast_api_intake_router.get(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description=f"Get a certain intake record by it id",
)
async def get_intake(
    intake_id: uuid.UUID,
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> Intake:
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    return await intake_crud.get(
        intake_id=intake_id,
        study_id=study_access.study.id,
        raise_exception_if_none=HTTPException(status_code=status.HTTP_404_NOT_FOUND),
    )


############
@fast_api_intake_router.post(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=Intake,
    description=f"Create intake record in certain interview. user must have at least 'interviewer'-permissions on study.",
)
async def create_intake(
    intake: Annotated[IntakeCreateAPI, Body()],
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> Intake:
    if not study_access.user_is_study_interviewer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of the study. otherwise caller could evade study permissions here by calling a interview id from another study.
    await assert_interview_is_part_of_study(
        study_id=study_access.study.id,
        interview_id=interview_id,
        interview_crud=interview_crud,
    )
    log.debug(f"create_intake(): intake: {intake}")
    log.debug(f"interview_id: {interview_id}")
    # ToDo: Casting to uuid is a hotfix here. it should be validated/transformed in the model itself
    # interview_id = uuid.UUID(interview_id)
    intake_create = IntakeCreate(interview_id=interview_id, **intake.model_dump())
    return await intake_crud.create(intake_create)


############
@fast_api_intake_router.patch(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    response_model=Intake,
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def update_intake(
    intake_id: uuid.UUID,
    intake: IntakeUpdate,
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
) -> Intake:
    if not study_access.user_is_study_interviewer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    return await intake_crud.update(update_obj=intake, id_=intake_id)


############
@fast_api_intake_router.delete(
    "/study/{study_id}/interview/{interview_id}/intake/{intake_id}",
    description=f"Update intake record. user must have at least 'interviewer'-permissions on study.",
)
async def delete_intake(
    intake_id: uuid.UUID,
    interview_id: Annotated[uuid.UUID, Path()],
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
):
    if not study_access.user_is_study_interviewer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not allowed to create intake",
        )
    # lets check if the the interview is part of study. otherwise caller could evade study permissions here by calling a interview id from another study.
    await assert_intake_is_part_of_study(
        study_id=study_access.study.id,
        intake_id=intake_id,
        intake_crud=intake_crud,
        interview_id=interview_id,
    )
    log.warning("ToDo: The med record are not deleted yet")
    return await intake_crud.delete(intake_id)


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/intake",
    response_model=PaginatedResponse[Intake],
    description=f"List all medicine intakes of one proband.",
)
async def list_all_intakes(
    proband_id: str,
    interview_id: Annotated[
        uuid.UUID, Query(description="Filter intakes by a certain interview.")
    ] = None,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(IntakeQueryParams),
) -> PaginatedResponse[Intake]:
    intakes = await intake_crud.list(
        filter_study_id=study_access.study.id,
        filter_proband_external_id=proband_id,
        filter_interview_id=interview_id,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await intake_crud.count(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=interview_id,
        ),
        offset=pagination.offset,
        count=len(intakes),
        items=intakes,
    )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/intake/details",
    response_model=PaginatedResponse[IntakeDetailListItem],
    description=f"List all medicine intakes of one proband, but as detailed table that includes Event, Interview and Drug details.",
)
async def list_all_intakes_detailed(
    proband_id: str,
    interview_id: Annotated[
        uuid.UUID, Query(description="Filter intakes by a certain interview.")
    ] = None,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    pagination: QueryParamsInterface = Depends(IntakeQueryParams),
) -> PaginatedResponse[IntakeDetailListItem]:
    intakes = await intake_crud.list_detailed(
        filter_study_id=study_access.study.id,
        filter_proband_external_id=proband_id,
        filter_interview_id=interview_id,
        pagination=pagination,
    )
    return PaginatedResponse(
        total_count=await intake_crud.count(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=interview_id,
        ),
        offset=pagination.offset,
        count=len(intakes),
        items=intakes,
    )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands last completed interview.",
    responses={status.HTTP_204_NO_CONTENT: {"description": "No interview exist yet"}},
)
async def list_all_intakes_of_last_completed_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    last_completed_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=True
    )
    if last_completed_interview:
        return await intake_crud.list(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_completed_interview.id,
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/last/intake/details",
    response_model=List[IntakeDetailListItem],
    description=f"List all medicine intakes of one probands last completed interview with all drug details attached.",
)
async def list_all_intakes_of_last_completed_interview_detailed(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> IntakeDetailListItem:
    last_completed_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=True
    )
    if last_completed_interview:
        return await intake_crud.list_detailed(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_completed_interview.id,
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )


############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of one probands current (non completed / Interview.interview_end_time_utc is None) interview.",
    responses={status.HTTP_204_NO_CONTENT: {"description": "No interview exist yet"}},
)
async def list_all_intakes_of_last_uncompleted_interview(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:
    last_uncompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if last_uncompleted_interview:
        return await intake_crud.list(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_uncompleted_interview.id,
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )


#############
@fast_api_intake_router.get(
    "/study/{study_id}/proband/{proband_id}/interview/current/intake/details",
    response_model=List[IntakeDetailListItem],
    description=f"List all medicine intakes of one probands last completed interview with all details attached.",
)
async def list_all_intakes_of_last_uncompleted_interview_detailed(
    proband_id: str,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> IntakeDetailListItem:
    last_incompleted_interview = await interview_crud.get_last_by_proband(
        study_id=study_access.study.id, proband_external_id=proband_id, completed=False
    )
    if last_incompleted_interview:
        return await intake_crud.list_detailed(
            filter_study_id=study_access.study.id,
            filter_proband_external_id=proband_id,
            filter_interview_id=last_incompleted_interview.id,
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
            headers={"X-Reason: No interview exist yet"},
        )


############
@fast_api_intake_router.get(
    "/study/{study_id}/interview/{interview_id}/intake",
    response_model=List[Intake],
    description=f"List all medicine intakes of interview.",
)
async def list_all_intakes_of_interview(
    interview_id: uuid.UUID,
    study_access: UserStudyAccess = Security(user_has_study_access),
    intake_crud: IntakeCRUD = Depends(IntakeCRUD.get_crud),
    interview_crud: InterviewCRUD = Depends(InterviewCRUD.get_crud),
) -> List[Intake]:

    return await intake_crud.list(
        filter_interview_id=interview_id, filter_study_id=study_access.study.id
    )
