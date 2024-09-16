from contextlib import asynccontextmanager
from fastapi import Depends
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


# from fastapi.security import

from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()

app = FastAPI(
    title="MedLog REST API",
    version="0.0.1",
    # openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    # debug=settings.debug,
)


def add_api_middleware(fastapiapp: FastAPI):
    # TODO FIX THIS: ONLY FOR DEV!!!
    allow_origins = []
    for oidc in config.AUTH_OIDC_PROVIDERS:
        allow_origins.append(
            str(oidc.DISCOVERY_ENDPOINT)
            .replace("//", "##")
            .split("/", 1)[0]
            .replace("##", "//")
        )

    allow_origins.extend(
        [
            str(config.CLIENT_URL).rstrip("/"),
            str(config.get_server_url()).rstrip("/"),
        ]
    )
    log.info(f"Origin allowed: {allow_origins}")
    fastapiapp.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    fastapiapp.add_middleware(
        SessionMiddleware, secret_key=config.SERVER_SESSION_SECRET.get_secret_value()
    )
