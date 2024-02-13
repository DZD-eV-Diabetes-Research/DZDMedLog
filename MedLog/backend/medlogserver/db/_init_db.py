from typing import AsyncGenerator, List

from fastapi import Depends

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from medlogserver.db._engine import db_engine
from medlogserver.db._session import get_async_session_context
from medlogserver.db.study.model import Study
from medlogserver.db.study_permission.model import StudyPermisson
from medlogserver.db.event.model import Event
from medlogserver.db.user.user import (
    User,
    UserCRUD,
    get_user_crud,
    get_users_crud_context,
)
from medlogserver.db.user.user_auth import (
    UserAuth,
    UserAuthCreate,
    UserAuthCRUD,
    get_user_auth_crud,
    get_user_auth_crud_context,
)
from medlogserver.db.interview.model import Interview
from medlogserver.db.intake.model import Intake

from medlogserver.db.user.user_auth_external_oidc_token import (
    UserAuthExternalOIDCToken,
)
from medlogserver.db.wido_gkv_arzneimittelindex.model import (
    Applikationsform,
    ATCKlassifikation,
    AmtlicheATCKlassifikation,
    Darreichungsform,
    AbweichungenAmtlicherATC,
    Hersteller,
    Normpackungsgroessen,
    ArzneimittelPriscus2,
    RecycelteArtikelnummern,
    Sondercodes,
    SondercodesTypes,
    StammAenderungen,
    Stammdatei,
)

from medlogserver.log import get_logger
from medlogserver.config import Config

log = get_logger()
config = Config()


# db_engine = create_async_engine(str(config.SQL_DATABASE_URL), echo=False, future=True)

from medlogserver.db._session import get_async_session


async def create_admin_if_not_exists():
    # https://stackoverflow.com/questions/75150942/how-to-get-a-session-from-async-session-generator-fastapi-sqlalchemy
    # session = await anext(get_async_session())
    async with get_async_session_context() as session:
        async with get_users_crud_context(session) as user_crud:
            user_crud: UserCRUD = user_crud
            admin_user = await user_crud.get_by_user_name(
                user_name=config.ADMIN_USER_NAME, show_deactivated=True
            )
        async with get_user_auth_crud_context(session) as user_auth_crud:
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


async def init_db():
    async with db_engine.begin() as conn:
        log.info(f"Init DB {config.SQL_DATABASE_URL}")
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        await create_admin_if_not_exists()
