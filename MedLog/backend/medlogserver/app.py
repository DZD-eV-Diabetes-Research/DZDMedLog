from fastapi import Depends
from fastapi import FastAPI

from medlogserver.api._routers import router

# from fastapi.security import
from fastapi_users import get_auth_router
from medlogserver.api.auth import auth_backend

app = FastAPI()
app.include_router(get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
