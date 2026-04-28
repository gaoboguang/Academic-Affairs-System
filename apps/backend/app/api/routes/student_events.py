from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.student_event import (
    AttendanceRecordListResponse,
    BehaviorRecordListResponse,
)
from app.services import student_events as service

attendance_router = APIRouter(prefix="/attendance", tags=["attendance"])
behavior_router = APIRouter(prefix="/behavior", tags=["behavior"])


@attendance_router.get("/template")
def download_attendance_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.templates_dir / "attendance_import_template.xlsx"
    return FileResponse(path, filename=Path(path).name)


@attendance_router.post("/import")
async def import_attendance_records(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    content = await file.read()
    return service.import_attendance_records(session, settings, filename=file.filename, content=content)


@attendance_router.get("/records", response_model=AttendanceRecordListResponse)
def list_attendance_records(
    student_id: int | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    session: Session = Depends(get_db_session),
) -> AttendanceRecordListResponse:
    return service.list_attendance_records(
        session,
        student_id=student_id,
        grade_id=grade_id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@behavior_router.get("/template")
def download_behavior_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.templates_dir / "behavior_import_template.xlsx"
    return FileResponse(path, filename=Path(path).name)


@behavior_router.post("/import")
async def import_behavior_records(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    content = await file.read()
    return service.import_behavior_records(session, settings, filename=file.filename, content=content)


@behavior_router.get("/records", response_model=BehaviorRecordListResponse)
def list_behavior_records(
    student_id: int | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=1000, ge=1, le=5000),
    session: Session = Depends(get_db_session),
) -> BehaviorRecordListResponse:
    return service.list_behavior_records(
        session,
        student_id=student_id,
        grade_id=grade_id,
        class_id=class_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
