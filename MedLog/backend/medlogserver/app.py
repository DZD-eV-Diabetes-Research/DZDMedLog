from contextlib import asynccontextmanager
import getversion
from fastapi import Depends
from fastapi import FastAPI
import getversion.plugin_setuptools_scm
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


# from fastapi.security import

import medlogserver
from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()

app = FastAPI(
    title="MedLog REST API",
    version=getversion.get_module_version(medlogserver)[0],
    # openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    # debug=settings.debug,
)


def add_api_middleware(fastapiapp: FastAPI):
    # TODO FIX THIS: ONLY FOR DEV!!!
    fastapiapp.add_middleware(
        CORSMiddleware,
        allow_origins=[config.CLIENT_URL, str(config.get_server_url()).rstrip("/")],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    fastapiapp.add_middleware(
        SessionMiddleware, secret_key=config.SERVER_SESSION_SECRET.get_secret_value()
    )
