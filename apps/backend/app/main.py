from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings, get_settings
from app.db.session import DatabaseManager
from app.exporters.templates import generate_import_templates
from app.utils.gaokao_sync import app_db_has_embedded_gaokao_tables


def _build_optional_gaokao_db_manager(settings: Settings) -> DatabaseManager | None:
    if app_db_has_embedded_gaokao_tables(settings.db_path):
        return None
    gaokao_db_path = settings.gaokao_db_path
    if gaokao_db_path is None or not gaokao_db_path.exists():
        return None
    if gaokao_db_path.resolve() == settings.db_path.resolve():
        return None
    return DatabaseManager(settings.gaokao_database_url, settings.debug)


def create_app(app_settings: Settings | None = None) -> FastAPI:
    settings = app_settings or get_settings()
    db_manager = DatabaseManager(settings.database_url, settings.debug)
    gaokao_db_manager = _build_optional_gaokao_db_manager(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ensure_runtime_directories(settings)
        db_manager.initialize()
        if gaokao_db_manager is not None:
            gaokao_db_manager.initialize()
        generate_import_templates(settings)
        yield
        if gaokao_db_manager is not None:
            gaokao_db_manager.dispose()
        db_manager.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = db_manager
    app.state.gaokao_db = gaokao_db_manager

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
