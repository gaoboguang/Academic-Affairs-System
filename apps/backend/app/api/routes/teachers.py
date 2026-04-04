from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.teacher import (
    TeacherListResponse,
    TeacherPayload,
    TeacherProfileRead,
    TeacherRead,
    TeacherTitleHistoryPayload,
    TeacherTitleHistoryRead,
    TeachingAssignmentPayload,
    TeachingAssignmentRead,
)
from app.services import teachers as service

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("", response_model=TeacherListResponse)
def list_teachers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    teacher_no: str | None = None,
    name: str | None = None,
    subject_id: int | None = None,
    title_code: str | None = None,
    is_head_teacher: bool | None = None,
    session: Session = Depends(get_db_session),
) -> TeacherListResponse:
    return service.list_teachers(
        session,
        page=page,
        page_size=page_size,
        teacher_no=teacher_no,
        name=name,
        subject_id=subject_id,
        title_code=title_code,
        is_head_teacher=is_head_teacher,
    )


@router.post("", response_model=TeacherRead)
def create_teacher(
    payload: TeacherPayload, session: Session = Depends(get_db_session)
) -> TeacherRead:
    return service.create_teacher(session, payload)


@router.get("/template")
def download_teacher_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.templates_dir / "teachers_import_template.xlsx"
    return FileResponse(path, filename=path.name)


@router.post("/import")
async def import_teachers(
    file: UploadFile = File(...),
    strategy: str = Form(default="skip_existing"),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    content = await file.read()
    return service.import_teachers(
        session,
        settings,
        filename=file.filename,
        content=content,
        strategy=strategy,
    )


@router.get("/export")
def export_teachers(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    result = service.export_teachers(session, settings)
    path = settings.project_root / result["file_path"]
    return FileResponse(path, filename=Path(path).name)


@router.get("/assignments", response_model=list[TeachingAssignmentRead])
def list_assignments(session: Session = Depends(get_db_session)) -> list[TeachingAssignmentRead]:
    return service.list_teaching_assignments(session)


@router.post("/assignments", response_model=TeachingAssignmentRead)
def create_assignment(
    payload: TeachingAssignmentPayload,
    session: Session = Depends(get_db_session),
) -> TeachingAssignmentRead:
    return service.create_teaching_assignment(session, payload)


@router.get("/{teacher_id}/profile", response_model=TeacherProfileRead)
def get_teacher_profile(
    teacher_id: int,
    session: Session = Depends(get_db_session),
) -> TeacherProfileRead:
    return service.get_teacher_profile(session, teacher_id)


@router.get("/{teacher_id}/title-histories", response_model=list[TeacherTitleHistoryRead])
def list_title_histories(
    teacher_id: int,
    session: Session = Depends(get_db_session),
) -> list[TeacherTitleHistoryRead]:
    return service.list_teacher_title_histories(session, teacher_id)


@router.put("/{teacher_id}/title-histories", response_model=list[TeacherTitleHistoryRead])
def save_title_histories(
    teacher_id: int,
    payload: list[TeacherTitleHistoryPayload],
    session: Session = Depends(get_db_session),
) -> list[TeacherTitleHistoryRead]:
    return service.save_teacher_title_histories(session, teacher_id, payload)


@router.get("/{teacher_id}", response_model=TeacherRead)
def get_teacher_detail(
    teacher_id: int,
    session: Session = Depends(get_db_session),
) -> TeacherRead:
    return service.get_teacher_detail(session, teacher_id)


@router.put("/{teacher_id}", response_model=TeacherRead)
def update_teacher(
    teacher_id: int,
    payload: TeacherPayload,
    session: Session = Depends(get_db_session),
) -> TeacherRead:
    return service.update_teacher(session, teacher_id, payload)
