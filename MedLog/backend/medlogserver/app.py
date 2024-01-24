from fastapi import Depends
from fastapi import FastAPI

from medlogserver.REST_api._routers import router

# from fastapi.security import
from medlogserver.REST_api.auth import auth_backend

app = FastAPI()
