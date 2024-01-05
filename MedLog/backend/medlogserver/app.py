from fastapi import Depends
from fastapi import FastAPI

from medlogserver.api._routers import router

app = FastAPI()
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
