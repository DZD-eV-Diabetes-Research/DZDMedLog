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
    full_path = Path(config.FRONTEND_FILES_DIR, path_name)
    log.debug(f"request frontend path {path_name} {full_path.is_file()}")
    if not path_name:
        file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
    if full_path.is_file():
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
    else:
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name, "index.html")
    return FileResponse(file)
