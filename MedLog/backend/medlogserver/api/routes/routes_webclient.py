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


if config.CLIENT_URL != config.get_server_url():

    @fast_api_webclient_router.get("/@vite/client")
    @fast_api_webclient_router.get("/@vite/{path:path}")
    async def serve_vite_client(request: Request, path: str = ""):
        """Special handler for Vite client imports."""
        # Construct the URL to the Vite client
        if path:
            full_url = f"{NUXT_DEV_SERVER}/@vite/{path}"
        else:
            full_url = f"{NUXT_DEV_SERVER}/@vite/client"

        log.debug(f"Serving Vite client: {full_url}")

        async with httpx.AsyncClient() as client:
            # Forward the request
            headers = dict(request.headers)
            headers.pop("host", None)
            headers["host"] = urlparse(NUXT_DEV_SERVER).netloc

            try:
                response = await client.get(full_url, headers=headers)

                # Ensure proper content type
                response_headers = dict(response.headers)
                response_headers["content-type"] = (
                    "application/javascript; charset=UTF-8"
                )
                response_headers["access-control-allow-origin"] = "*"

                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers,
                )
            except Exception as e:
                log.error(f"Error serving Vite client: {e}")
                return Response(
                    content=f"Error connecting to Vite dev server: {str(e)}",
                    status_code=502,
                    media_type="text/plain",
                )

    # The client runs on a different server
    @fast_api_webclient_router.get("/{path_name:path}")
    async def serve_frontend(request: Request, path_name: Optional[str] = None):
        """Proxy HTTP requests to the Nuxt dev server with improved handling for CSS modules."""
        path_name = path_name or ""
        full_url = urljoin(NUXT_DEV_SERVER + "/", path_name)

        log.debug(f"Proxying request to: {full_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare headers
            headers = dict(request.headers)
            headers.pop("host", None)
            headers["host"] = urlparse(NUXT_DEV_SERVER).netloc

            # Check if the request has Accept header asking for JavaScript
            accept_header = headers.get("accept", "")
            is_module_request = (
                "module" in accept_header or "javascript" in accept_header
            )

            # Handle Import CSS as Module case - critical for Vite to work correctly
            if path_name.endswith(".css") and is_module_request:
                # For CSS imported as modules, Vite expects to handle this specially
                headers["accept"] = "application/javascript"

            try:
                # Stream the response
                async with client.stream(
                    method=request.method,
                    url=full_url,
                    headers=headers,
                    cookies=request.cookies,
                    params=request.query_params,
                    content=await request.body(),
                    follow_redirects=True,
                ) as response:
                    # Process response headers
                    response_headers = dict(response.headers)

                    # Remove problematic headers
                    for header in [
                        "content-length",
                        "transfer-encoding",
                        "content-encoding",
                    ]:
                        response_headers.pop(header, None)

                    # Set CORS headers
                    response_headers["access-control-allow-origin"] = "*"
                    response_headers["access-control-allow-methods"] = (
                        "GET, POST, PUT, DELETE, OPTIONS"
                    )
                    response_headers["access-control-allow-headers"] = "*"

                    # Read content
                    content = await response.aread()

                    # Critical: For CSS files requested as modules, serve them as JavaScript
                    original_content_type = response_headers.get("content-type", "")
                    if path_name.endswith(".css") and is_module_request:
                        # This is the key fix - CSS imported as modules should be served as JS
                        response_headers["content-type"] = (
                            "application/javascript; charset=UTF-8"
                        )

                        # For debugging
                        log.debug(f"Serving CSS as JS module: {path_name}")
                    elif path_name.endswith((".js", ".mjs")):
                        response_headers["content-type"] = (
                            "application/javascript; charset=UTF-8"
                        )
                    elif path_name.endswith(".vue"):
                        response_headers["content-type"] = (
                            "application/javascript; charset=UTF-8"
                        )

                    return Response(
                        content=content,
                        status_code=response.status_code,
                        headers=response_headers,
                    )

            except httpx.RequestError as e:
                log.error(f"Proxy error for {full_url}: {e}")
                return Response(
                    content=f"Error connecting to Nuxt dev server: {str(e)}",
                    status_code=502,
                    media_type="text/plain",
                )

    # Addionally we proxy websocket connections just in case we run a nuxt dev server behind the client url
    @fast_api_webclient_router.websocket("/{path_name:path}")
    async def websocket_proxy(websocket: WebSocket, path_name: str = ""):
        """Detect and correctly route WebSocket connections for Vite HMR and Nuxt."""

        # Build WebSocket URL with query parameters
        ws_url = urljoin(NUXT_DEV_SERVER.replace("http", "ws"), path_name)

        # Pass along query parameters if present
        if websocket.query_params:
            query_string = "&".join(
                [f"{k}={v}" for k, v in websocket.query_params.items()]
            )
            ws_url = f"{ws_url}?{query_string}"

        log.info(f"Proxying WebSocket to: '{ws_url}'")

        try:
            await websocket.accept()

            # Connect to the target WebSocket with proper headers forwarding
            headers = dict(websocket.headers)
            headers["host"] = "localhost:3000"  # Set appropriate host

            async with websockets.connect(
                ws_url,
                open_timeout=10,  # Increased timeout
                additional_headers=headers,
                subprotocols=websocket.scope.get("subprotocols", []),
            ) as client_ws:
                # Forward messages between client and server
                async def client_to_server():
                    try:
                        while True:
                            try:
                                data = await websocket.receive()
                                if "text" in data:
                                    await client_ws.send(data["text"])
                                elif "bytes" in data:
                                    await client_ws.send(data["bytes"])
                            except RuntimeError as e:
                                # Handle "Cannot call receive once disconnected" error
                                if "disconnect message" in str(e):
                                    log.debug("Client websocket disconnected")
                                    break
                                else:
                                    raise
                    except WebSocketDisconnect:
                        log.debug("Client disconnected")
                    except Exception as e:
                        log.error(f"Error in client_to_server: {e}")
                    finally:
                        # Signal server_to_client to stop
                        try:
                            # Use close() directly without checking closed attribute
                            await client_ws.close()
                        except Exception as e:
                            log.debug(f"Error closing client websocket: {e}")

                async def server_to_client():
                    try:
                        while True:
                            try:
                                message = await client_ws.recv()
                                if isinstance(message, str):
                                    await websocket.send_text(message)
                                else:
                                    await websocket.send_bytes(message)
                            except websockets.exceptions.ConnectionClosed:
                                log.debug("Server websocket closed")
                                break
                    except WebSocketDisconnect:
                        log.debug("Client disconnected during server_to_client")
                    except Exception as e:
                        log.error(f"Error forwarding WebSocket message: {e}")
                    finally:
                        # Ensure the client websocket is closed if it's still open
                        try:
                            await websocket.close()
                        except Exception:
                            pass

                # Run both tasks concurrently and wait for either to complete
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(client_to_server()),
                        asyncio.create_task(server_to_client()),
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                # Cancel any pending tasks and wait for them to complete
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        except websockets.exceptions.InvalidHandshake as e:
            log.error(f"WebSocket handshake failed to '{ws_url}'! Is Vite running?")
            await websocket.close(1011, f"Handshake failed: {str(e)[:100]}")
        except asyncio.TimeoutError:
            log.error(
                f"WebSocket connection timed out to '{ws_url}'! Check Vite dev server."
            )
            await websocket.close(1011, "Connection timed out")
        except Exception as e:
            log.error(f"WebSocket proxy error to '{ws_url}': {e}")
            try:
                await websocket.close(1011, f"Proxy error: {str(e)[:100]}")
            except Exception:
                pass

else:
    # We use the compiled static file client
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
        if Path(file).exists():
            return FileResponse(file)
        # SPA Fallback. Let the Nuxt Client router parse URL
        return FileResponse(f"{config.FRONTEND_FILES_DIR}/index.html")
