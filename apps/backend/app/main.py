from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings, get_settings
from app.db.session import DatabaseManager
from app.exporters.templates import generate_import_templates
from app.services.auth import PUBLIC_API_PATHS, build_context_from_token


_logger = logging.getLogger("local_edu.unhandled")
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _build_attach_databases(settings: Settings) -> dict[str, "Path"]:  # type: ignore[name-defined]
    """Return the alias→path map of secondary SQLite files to ATTACH at connect.

    The gaokao raw tables now live in the sidecar database. Attaching it under
    the `gaokao` alias also exposes the tables un-qualified, so existing SQL
    like `FROM gaokao_admission_result` keeps working without code changes.
    """
    from pathlib import Path

    attach: dict[str, Path] = {}
    sidecar_path = settings.gaokao_db_path
    if sidecar_path is None:
        return attach
    sidecar_resolved = sidecar_path.resolve() if sidecar_path.exists() else sidecar_path
    if not sidecar_resolved.exists():
        return attach
    if sidecar_resolved == settings.db_path.resolve():
        return attach
    attach["gaokao"] = sidecar_resolved
    return attach


def create_app(app_settings: Settings | None = None) -> FastAPI:
    settings = app_settings or get_settings()
    attach_databases = _build_attach_databases(settings)
    db_manager = DatabaseManager(
        settings.database_url,
        settings.debug,
        attach_databases=attach_databases,
    )

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
    # Legacy alias kept for backward compatibility; the dedicated sidecar
    # session has been merged into the main one via ATTACH.
    app.state.gaokao_db = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _is_teacher_forbidden(path: str, method: str) -> str | None:
        if path.startswith("/api/admin"):
            return "需要管理员权限"
        if path.startswith("/api/system"):
            return "需要管理员权限"
        if path.startswith("/api/teachers"):
            return "需要管理员权限"
        if path.startswith("/api/recommendations") or path.startswith("/api/gaokao"):
            return "需要管理员权限"
        if path.startswith("/api/base") and method.upper() != "GET":
            return "需要管理员权限"
        if path.startswith("/api/students/bulk-") or path.startswith("/api/students/class-transfer"):
            return "需要管理员权限"
        return None

    @app.middleware("http")
    async def _auth_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        if not settings.auth_required or not request.url.path.startswith(settings.api_prefix):
            return await call_next(request)
        if request.method.upper() == "OPTIONS" or request.url.path in PUBLIC_API_PATHS:
            return await call_next(request)

        token = request.cookies.get(settings.auth_cookie_name)
        if not token:
            return JSONResponse(status_code=401, content={"detail": "请先登录"})

        with db_manager.session_scope() as auth_session:
            context = build_context_from_token(
                auth_session,
                token,
                request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
                or (request.client.host if request.client else None),
            )
            if context is None:
                return JSONResponse(status_code=401, content={"detail": "登录已失效，请重新登录"})
            forbidden_detail = None if context.is_admin else _is_teacher_forbidden(request.url.path, request.method)
            if forbidden_detail:
                return JSONResponse(status_code=403, content={"detail": forbidden_detail})
            if request.method.upper() in _UNSAFE_METHODS and request.headers.get("x-csrf-token") != context.csrf_token:
                return JSONResponse(status_code=403, content={"detail": "CSRF 校验失败，请刷新页面后重试"})
            request.state.auth_context = context
        return await call_next(request)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the full traceback locally so we can debug, but never echo the
        # raw error text back to the teacher — it could expose SQL fragments
        # or absolute file paths.
        _logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务暂时无法处理该操作，请稍后再试或联系管理员。"},
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
