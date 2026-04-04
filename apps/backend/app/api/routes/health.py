from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings

router = APIRouter(tags=["system"])


@router.get("/system/health")
def health_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/system/templates")
def list_templates(settings: Settings = Depends(get_settings)) -> dict[str, list[str]]:
    files = sorted(path.name for path in settings.templates_dir.glob("*.xlsx"))
    return {"items": files}


@router.get("/system/files")
def download_runtime_file(
    path: str = Query(..., description="相对项目根目录的文件路径"),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    project_root = settings.project_root.resolve()
    target = (project_root / path).resolve()
    if project_root not in target.parents and target != project_root:
        raise HTTPException(status_code=400, detail="非法文件路径")
    if not target.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(target, filename=Path(target).name)
