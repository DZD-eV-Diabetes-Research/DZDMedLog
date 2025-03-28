from typing import Annotated, Sequence, List, Type, Optional
import os
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
from medlogserver.config import Config

config = Config()

from medlogserver.log import get_logger

log = get_logger()


fast_api_webclient_router: APIRouter = APIRouter()


@fast_api_webclient_router.get("/{path_name:path}")
async def serve_frontend(path_name: Optional[str] = None):
    if path_name:
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
        if Path(file).is_dir():
            file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
    else:
        file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
    return FileResponse(file)
