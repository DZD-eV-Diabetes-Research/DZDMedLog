from typing import Annotated, Sequence, List, Type, Optional
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin
from fastapi import (
    FastAPI,
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse, HTMLResponse, Response
from medlogserver.config import Config
import httpx
import websockets
import asyncio

config = Config()

from medlogserver.log import get_logger

log = get_logger()


NUXT_DEV_SERVER = "http://localhost:3000"


fast_api_webclient_router: APIRouter = APIRouter()


# We use the compiled static file client
@fast_api_webclient_router.get("/{path_name:path}")
async def serve_frontend(req: Request, path_name: Optional[str] = None):
    headers = {}

    full_path = Path(config.FRONTEND_FILES_DIR, path_name)
    log.debug(f"request frontend path {path_name} {full_path.is_file()}")
    file: str = None
    if not path_name:
        file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
    if full_path.is_file():
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
    if full_path.is_dir():
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name, "index.html")
    if file is not None and Path(file).exists():
        if file.endswith(".css"):
            headers["content-type"] = "text/css; charset=UTF-8"
        elif file.endswith(".js"):
            headers["content-type"] = "application/javascript; charset=UTF-8"
        elif file.endswith(".html"):
            headers["content-type"] = "text/html; charset=UTF-8"
        elif file.endswith(".json"):
            headers["content-type"] = "application/json; charset=UTF-8"
        log.debug(
            f"Response on path_name:'{path_name}' file:'{file}' (RespHeaders: {headers} ReqHeaders: {req.headers})"
        )
        return FileResponse(file, headers=headers)
    elif "_nuxt" in path_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{path_name} could not be found.",
        )
    # SPA Fallback. Let the Nuxt Client router parse URL
    headers["content-type"] = "text/html; charset=UTF-8"
    log.debug(
        f"Response on path_name:'{path_name}' with default index '{config.FRONTEND_FILES_DIR}/index.html' (RespHeaders: {headers} ReqHeaders: {req.headers})"
    )
    return FileResponse(f"{config.FRONTEND_FILES_DIR}/index.html", headers=headers)
