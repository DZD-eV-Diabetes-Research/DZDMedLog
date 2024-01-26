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

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=config.SERVER_SESSION_SECRET)

# TODO FIX THIS: ONLY FOR DEV
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
