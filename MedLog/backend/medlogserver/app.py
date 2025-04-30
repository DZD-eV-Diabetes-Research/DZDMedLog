from typing import Dict, List, Callable, Awaitable
from contextlib import asynccontextmanager
import getversion
import inspect
from fastapi import Depends
from fastapi import FastAPI
import getversion.plugin_setuptools_scm
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from medlogserver.api.routers_map import mount_fast_api_routers

# from fastapi.security import

import medlogserver
from medlogserver.config import Config
from medlogserver.log import get_logger


log = get_logger()
config = Config()

from dataclasses import dataclass


@dataclass
class AppLifespanCallback:
    func: Callable
    params: Dict | None = None

    def is_async(self):
        return inspect.iscoroutinefunction(self.func)


class FastApiAppContainer:
    def __init__(self):
        self.shutdown_callbacks: List[AppLifespanCallback] = []
        self.startup_callbacks: List[AppLifespanCallback] = []
        self.app = FastAPI(
            title="MedLog REST API",
            version=getversion.get_module_version(medlogserver)[0],
            # openapi_url=f"{settings.api_v1_prefix}/openapi.json",
            # debug=settings.debug,
            lifespan=self._app_lifespan,
        )
        self._mount_routers()
        self._apply_api_middleware()

    def add_startup_callback(self, func: Callable, params: Dict | None = None):
        self.startup_callbacks.append(AppLifespanCallback(func=func, params=params))

    def add_shutdown_callback(self, func: Callable, params: Dict | None = None):
        self.shutdown_callbacks.append(AppLifespanCallback(func=func, params=params))

    @asynccontextmanager
    async def _app_lifespan(self, app: FastAPI):
        # https://fastapi.tiangolo.com/advanced/events/#lifespan
        for cb in self.startup_callbacks:
            params = cb.params if cb.params else {}
            if cb.is_async():
                await cb.func(**params)
            else:
                cb.func(**params)

        yield
        for cb in self.shutdown_callbacks:
            params = cb.params if cb.params else {}
            if cb.is_async():
                await cb.func(**params)
            else:
                cb.func(**params)

    def _apply_api_middleware(self):
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
        allow_origins = set(allow_origins)
        log.info(f"Origin allowed: {allow_origins}")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=set(allow_origins),
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=config.SERVER_SESSION_SECRET.get_secret_value(),
        )

    def _mount_routers(self):
        mount_fast_api_routers(self.app)
