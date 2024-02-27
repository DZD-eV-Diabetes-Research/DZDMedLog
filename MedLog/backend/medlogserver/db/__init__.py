from typing import Dict, Type
from medlogserver.db._base_model import BaseModel
from medlogserver.db._base_crud import CRUDBase
from medlogserver.db.event.model import Event, EventCreate, EventRead, EventUpdate
from medlogserver.db.event.crud import EventCRUD
from medlogserver.db.intake.model import (
    Intake,
    IntakeCreate,
    IntakeRegularOrAsNeededAnswers,
    IntakeUpdate,
    IntervalOfDailyDoseAnswers,
)
from medlogserver.db.intake.crud import IntakeCRUD
from medlogserver.db.interview.model import Interview, InterviewCreate, InterviewUpdate
from medlogserver.db.interview.crud import InterviewCRUD
from medlogserver.db.study.model import Study, StudyCreate, StudyUpdate
from medlogserver.db.study.crud import StudyCRUD
from medlogserver.db.study_permission.model import (
    StudyPermisson,
    StudyPermissonUpdate,
    StudyPermissonHumanReadeable,
)
from medlogserver.db.study_permission.crud import StudyPermissonCRUD
from medlogserver.db.user.model import (
    User,
    UserCreate,
    UserUpdate,
    UserUpdateByAdmin,
    UserUpdateByUser,
)
from medlogserver.db.user.crud import UserCRUD
from medlogserver.db.user_auth.model import UserAuth, UserAuthCreate, UserAuthUpdate
from medlogserver.db.user_auth.crud import UserAuthCRUD
