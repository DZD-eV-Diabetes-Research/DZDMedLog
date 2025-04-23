from medlogserver.model.event import Event
from medlogserver.model.intake import Intake
from medlogserver.model.interview import Interview
from medlogserver.model.study import Study
from medlogserver.model.study_permission import StudyPermisson
from medlogserver.model.user_auth_external_oidc_token import UserAuthExternalOIDCToken
from medlogserver.model.user_auth_refresh_token import UserAuthRefreshToken
from medlogserver.model.user_auth import UserAuth
from medlogserver.model.user import User
from medlogserver.model.worker_job import WorkerJob
from medlogserver.model.drug_data.drug_attr_field_definition import (
    DrugAttrFieldDefinition,
)
from medlogserver.model.drug_data.drug_attr_field_lov_item import DrugAttrFieldLovItem
from medlogserver.model.drug_data.drug_attr import (
    DrugVal,
    DrugValRef,
    DrugValMulti,
    DrugValMultiRef,
)
from medlogserver.model.drug_data.drug_code_system import DrugCodeSystem
from medlogserver.model.drug_data.drug_code import DrugCode
from medlogserver.model.drug_data.drug_dataset_version import DrugDataSetVersion
from medlogserver.model.drug_data.drug import DrugData


from medlogserver.model.user_auth_external_oidc_token import UserAuthExternalOIDCToken

all_tables = [
    Event,
    Intake,
    Interview,
    Study,
    StudyPermisson,
    UserAuthExternalOIDCToken,
    UserAuthRefreshToken,
    UserAuth,
    User,
    WorkerJob,
    DrugAttrFieldDefinition,
    DrugAttrFieldLovItem,
    DrugVal,
    DrugValRef,
    DrugValMulti,
    DrugValMultiRef,
    DrugCodeSystem,
    DrugCode,
    DrugDataSetVersion,
    DrugData,
]
