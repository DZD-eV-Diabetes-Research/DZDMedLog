from typing import Annotated, Sequence, List, Type, Optional
import os
from pathlib import Path
from urllib.parse import urlparse, urljoin
from fastapi import FastAPI, APIRouter, Request, WebSocket, WebSocketDisconnect
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
async def serve_frontend(path_name: Optional[str] = None):
    headers = {}

    full_path = Path(config.FRONTEND_FILES_DIR, path_name)
    log.debug(f"request frontend path {path_name} {full_path.is_file()}")
    if not path_name:
        file = os.path.join(config.FRONTEND_FILES_DIR, "index.html")
    if full_path.is_file():
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name)
    else:
        file = os.path.join(config.FRONTEND_FILES_DIR, path_name, "index.html")
    if Path(file).exists():
        if path_name.endswith(".css"):
            headers["content-type"] = "text/css; charset=UTF-8"
        elif path_name.endswith(".js"):
            headers["content-type"] = "application/javascript; charset=UTF-8"
        elif path_name.endswith(".html"):
            headers["content-type"] = "text/html; charset=UTF-8"
        elif path_name.endswith(".json"):
            headers["content-type"] = "application/json; charset=UTF-8"
        return FileResponse(file, headers=headers)
    # SPA Fallback. Let the Nuxt Client router parse URL
    headers["content-type"] = "text/html; charset=UTF-8"
    return FileResponse(f"{config.FRONTEND_FILES_DIR}/index.html", headers=headers)
