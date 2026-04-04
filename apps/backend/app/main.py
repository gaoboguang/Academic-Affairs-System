from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings, get_settings
from app.db.session import DatabaseManager
from app.exporters.templates import generate_import_templates


def create_app(app_settings: Settings | None = None) -> FastAPI:
    settings = app_settings or get_settings()
    db_manager = DatabaseManager(settings.database_url, settings.debug)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_runtime_directories(settings)
        db_manager.initialize()
        generate_import_templates(settings)
        yield
        db_manager.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = db_manager

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()

