from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.utils.files import resolve_project_file_path

router = APIRouter(tags=["health"])


@router.get("/system/health")
def health_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/system/files")
def download_runtime_file(
    path: str = Query(..., description="相对项目根目录的文件路径"),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    target = resolve_project_file_path(settings.project_root, path)
    return FileResponse(target, filename=Path(target).name)
