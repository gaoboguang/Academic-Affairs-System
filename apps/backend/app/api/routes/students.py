from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.student import (
    StudentAttachmentPayload,
    StudentAttachmentSummary,
    StudentCareerPreferencePayload,
    StudentCareerPreferenceRead,
    StudentListResponse,
    StudentPayload,
    StudentProfileRead,
    StudentRead,
)
from app.services import students as service
from app.utils.files import resolve_allowed_file_path

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=StudentListResponse)
def list_students(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=1000),
    student_no: str | None = None,
    name: str | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    status: str | None = None,
    student_type: str | None = None,
    art_track: str | None = None,
    session: Session = Depends(get_db_session),
) -> StudentListResponse:
    return service.list_students(
        session,
        page=page,
        page_size=page_size,
        student_no=student_no,
        name=name,
        grade_id=grade_id,
        class_id=class_id,
        status=status,
        student_type=student_type,
        art_track=art_track,
    )


@router.post("", response_model=StudentRead)
def create_student(
    payload: StudentPayload, session: Session = Depends(get_db_session)
) -> StudentRead:
    return service.create_student(session, payload)


@router.get("/template")
def download_student_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.templates_dir / "students_import_template.xlsx"
    return FileResponse(path, filename=path.name)


@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    strategy: str = Form(default="skip_existing"),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    content = await file.read()
    return service.import_students(
        session,
        settings,
        filename=file.filename,
        content=content,
        strategy=strategy,
    )


@router.get("/export")
def export_students(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    result = service.export_students(session, settings)
    path = resolve_allowed_file_path(
        result["file_path"],
        allowed_roots=[settings.exports_dir],
        project_root=settings.project_root,
    )
    return FileResponse(path, filename=Path(path).name)


@router.get("/{student_id}/profile", response_model=StudentProfileRead)
def get_student_profile(
    student_id: int,
    session: Session = Depends(get_db_session),
) -> StudentProfileRead:
    return service.get_student_profile(session, student_id)


@router.get("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead | None)
def get_student_career_preference(
    student_id: int,
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead | None:
    return service.get_student_career_preference(session, student_id)


@router.post("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead)
def create_student_career_preference(
    student_id: int,
    payload: StudentCareerPreferencePayload,
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead:
    return service.create_student_career_preference(session, student_id, payload)


@router.put("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead)
def update_student_career_preference(
    student_id: int,
    payload: StudentCareerPreferencePayload,
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead:
    return service.update_student_career_preference(session, student_id, payload)


@router.get("/{student_id}/attachments", response_model=list[StudentAttachmentSummary])
def list_student_attachments(
    student_id: int,
    session: Session = Depends(get_db_session),
) -> list[StudentAttachmentSummary]:
    return service.list_student_attachments(session, student_id)


@router.post("/{student_id}/attachments", response_model=StudentAttachmentSummary)
def create_student_attachment(
    student_id: int,
    payload: StudentAttachmentPayload,
    session: Session = Depends(get_db_session),
) -> StudentAttachmentSummary:
    return service.create_student_attachment(session, student_id, payload)


@router.delete("/{student_id}/attachments/{attachment_id}")
def delete_student_attachment(
    student_id: int,
    attachment_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_student_attachment(session, student_id, attachment_id)


@router.get("/{student_id}", response_model=StudentRead)
def get_student_detail(
    student_id: int, session: Session = Depends(get_db_session)
) -> StudentRead:
    return service.get_student_detail(session, student_id)


@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentPayload,
    session: Session = Depends(get_db_session),
) -> StudentRead:
    return service.update_student(session, student_id, payload)
