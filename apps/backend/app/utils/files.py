from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException


UPLOAD_CATEGORY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,49}$")


def validate_upload_category(category: str | None) -> str:
    value = (category or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail="上传分类不能为空")
    if not UPLOAD_CATEGORY_PATTERN.fullmatch(value):
        raise HTTPException(status_code=400, detail="上传分类不合法")
    return value


def resolve_project_file_path(
    project_root: Path,
    relative_path: str | Path,
    *,
    not_found_detail: str = "文件不存在",
    invalid_detail: str = "非法文件路径",
) -> Path:
    base = project_root.resolve()
    raw_path = Path(relative_path)
    if raw_path.is_absolute():
        raise HTTPException(status_code=400, detail=invalid_detail)
    target = (base / raw_path).resolve(strict=False)
    _ensure_within_base(base, target, invalid_detail=invalid_detail)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=not_found_detail)
    return target


def resolve_allowed_file_path(
    file_path: str | Path,
    *,
    allowed_roots: list[Path],
    project_root: Path,
    not_found_detail: str = "文件不存在",
    invalid_detail: str = "非法文件路径",
) -> Path:
    raw_path = Path(file_path)
    if raw_path.is_absolute():
        target = raw_path.resolve(strict=False)
    else:
        target = (project_root.resolve() / raw_path).resolve(strict=False)

    resolved_roots = [root.resolve() for root in allowed_roots]
    if not any(target == base or base in target.parents for base in resolved_roots):
        raise HTTPException(status_code=400, detail=invalid_detail)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=not_found_detail)
    return target


def resolve_named_file_in_directory(
    base_dir: Path,
    file_name: str,
    *,
    not_found_detail: str = "文件不存在",
    invalid_detail: str = "非法文件路径",
) -> Path:
    safe_name = Path(file_name).name
    base = base_dir.resolve()
    target = (base / safe_name).resolve(strict=False)
    _ensure_within_base(base, target, invalid_detail=invalid_detail)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=not_found_detail)
    return target


def _ensure_within_base(base: Path, target: Path, *, invalid_detail: str) -> None:
    if target != base and base not in target.parents:
        raise HTTPException(status_code=400, detail=invalid_detail)
