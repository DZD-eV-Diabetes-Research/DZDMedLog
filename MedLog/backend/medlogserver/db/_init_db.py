from typing import AsyncGenerator, List, Optional

from fastapi import Depends
from pathlib import Path, PurePath
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from medlogserver.db._engine import db_engine
from medlogserver.db._session import get_async_session_context
from medlogserver.db.study.model import Study
from medlogserver.db.study_permission.model import StudyPermisson
from medlogserver.db.event.model import Event
from medlogserver.db.user.crud import (
    User,
    UserCRUD,
)
from medlogserver.db.user_auth.crud import (
    UserAuth,
    UserAuthCreate,
    UserAuthCRUD,
)
from medlogserver.db.interview.model import Interview
from medlogserver.db.intake.model import Intake

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model import (
    AiDataVersion,
    Applikationsform,
    ATCai,
    ATCAmtlich,
    Darreichungsform,
    ATCErgaenzungAmtlich,
    Hersteller,
    Normpackungsgroessen,
    Priscus2PZN,
    RecycledPZN,
    Sondercodes,
    SondercodeBedeutung,
    StammAenderungen,
    Stamm,
)
from medlogserver.db.wido_gkv_arzneimittelindex.crud import (
    AiDataVersionCRUD,
    get_ai_data_version_crud_context,
)

from medlogserver.log import get_logger
from medlogserver.config import Config

log = get_logger()
config = Config()


if config.DRUG_SEARCHENGINE_CLASS == "GenericSQLDrugSearch":
    from medlogserver.db.wido_gkv_arzneimittelindex.drug_search.search_module_generic_sql import (
        GenericSQLDrugSearchState,
        GenericSQLDrugSearchCache,
    )

# db_engine = create_async_engine(str(config.SQL_DATABASE_URL), echo=False, future=True)

from medlogserver.db._session import get_async_session


async def create_admin_if_not_exists():
    # https://stackoverflow.com/questions/75150942/how-to-get-a-session-from-async-session-generator-fastapi-sqlalchemy
    # session = await anext(get_async_session())
    async with get_async_session_context() as session:
        async with UserCRUD.crud_context(session) as user_crud:
            user_crud: UserCRUD = user_crud
            admin_user = await user_crud.get_by_user_name(
                user_name=config.ADMIN_USER_NAME, show_deactivated=True
            )
        async with UserAuthCRUD.crud_context(session) as user_auth_crud:
            if admin_user is None:
                log.info(f"Creating admin user {config.ADMIN_USER_NAME}")
                admin_user = User(
                    user_name=config.ADMIN_USER_NAME,
                    email=config.ADMIN_USER_EMAIL,
                    deactivated=False,
                    roles=[config.ADMIN_ROLE_NAME],
                )
                admin_user = await user_crud.create(admin_user)
                admin_user_auth = UserAuthCreate(
                    user_id=admin_user.id, password=config.ADMIN_USER_PW
                )
                log.info(f"admin_user_auth {admin_user_auth}")
                await user_auth_crud.create(admin_user_auth)


async def get_current_ai_data_version() -> Optional[AiDataVersion]:
    async with get_async_session_context() as session:
        async with get_ai_data_version_crud_context(session) as ai_data_version_crud:
            return await ai_data_version_crud.get_current(none_is_ok=True)


async def init_drugsearch():
    current_ai_data_version = await get_current_ai_data_version()
    if current_ai_data_version is not None:
        from medlogserver.db.wido_gkv_arzneimittelindex.drug_search.search_module_generic_sql import (
            GenericSQLDrugSearchEngine,
        )

        search_engine = GenericSQLDrugSearchEngine(
            target_ai_data_version=current_ai_data_version
        )
        await search_engine.build_index()


async def provision_drug_data():
    from medlogserver.worker.wido_gkv_arzneimittelindex_importer import load_data

    prov_data_dir = Path(config.DRUG_TABLE_PROVISIONING_SOURCE_DIR)
    prov_stamm_path = Path(PurePath(prov_data_dir, "stamm.txt"))
    if prov_stamm_path.exists() and prov_stamm_path.is_file():
        await load_data(source_data_dir=config.DRUG_TABLE_PROVISIONING_SOURCE_DIR)
    elif prov_data_dir is not None:
        log.warning(
            "'DRUG_TABLE_PROVISIONING_SOURCE_DIR' is defined in config but no source data dir found. Will skip drug data provsioning"
        )


async def init_db():
    async with db_engine.begin() as conn:
        log.info(f"Init DB {config.SQL_DATABASE_URL}")
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        await create_admin_if_not_exists()
        await provision_drug_data()
        await init_drugsearch()
