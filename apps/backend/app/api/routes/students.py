from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings, require_admin, require_permission
from app.core.config import Settings
from app.schemas.student import (
    StudentAttachmentPayload,
    StudentAttachmentSummary,
    StudentBulkDeleteExecuteRequest,
    StudentBulkDeleteExecuteResponse,
    StudentBulkDeletePreviewRequest,
    StudentBulkDeletePreviewResponse,
    StudentCareerPreferencePayload,
    StudentCareerPreferenceRead,
    StudentClassTransferExecuteRequest,
    StudentClassTransferExecuteResponse,
    StudentClassTransferHistoryItem,
    StudentClassTransferPreviewRequest,
    StudentClassTransferPreviewResponse,
    StudentListResponse,
    StudentPayload,
    StudentProfileRead,
    StudentRead,
    StudentTeacherCommentListResponse,
    StudentTeacherCommentPayload,
    StudentTeacherCommentRead,
)
from app.services import students as service
from app.services.auth import AuthContext
from app.utils.files import resolve_allowed_file_path

router = APIRouter(prefix="/students", tags=["students"])


def _scope_class_ids(current_user: AuthContext) -> set[int] | None:
    return None if current_user.is_admin else set(current_user.class_scope_ids)


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
    include_inactive: bool = Query(default=False),
    current_user: AuthContext = Depends(require_permission("students:read")),
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
        include_inactive=include_inactive,
        scope_class_ids=_scope_class_ids(current_user),
    )


@router.post("", response_model=StudentRead)
def create_student(
    payload: StudentPayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentRead:
    return service.create_student(
        session,
        payload,
        scope_class_ids=_scope_class_ids(current_user),
        actor=current_user,
    )


@router.get("/template")
def download_student_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    path = settings.templates_dir / "students_import_template.xlsx"
    return FileResponse(path, filename=path.name)


@router.post("/import")
async def import_students(
    file: UploadFile = File(...),
    strategy: str = Form(default="skip_existing"),
    _: AuthContext = Depends(require_admin),
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
    _: AuthContext = Depends(require_admin),
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


@router.post("/bulk-delete/preview", response_model=StudentBulkDeletePreviewResponse)
def preview_student_bulk_delete(
    payload: StudentBulkDeletePreviewRequest,
    _: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> StudentBulkDeletePreviewResponse:
    return service.preview_student_bulk_delete(session, payload)


@router.post("/bulk-delete", response_model=StudentBulkDeleteExecuteResponse)
def execute_student_bulk_delete(
    payload: StudentBulkDeleteExecuteRequest,
    _: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> StudentBulkDeleteExecuteResponse:
    return service.execute_student_bulk_delete(session, payload)


@router.post("/class-transfer/preview", response_model=StudentClassTransferPreviewResponse)
def preview_student_class_transfer(
    payload: StudentClassTransferPreviewRequest,
    _: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> StudentClassTransferPreviewResponse:
    return service.preview_student_class_transfer(session, payload)


@router.post("/class-transfer", response_model=StudentClassTransferExecuteResponse)
def execute_student_class_transfer(
    payload: StudentClassTransferExecuteRequest,
    _: AuthContext = Depends(require_admin),
    session: Session = Depends(get_db_session),
) -> StudentClassTransferExecuteResponse:
    return service.execute_student_class_transfer(session, payload)


@router.get("/{student_id}/profile", response_model=StudentProfileRead)
def get_student_profile(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> StudentProfileRead:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.get_student_profile(session, student_id)


@router.get("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead | None)
def get_student_career_preference(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead | None:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.get_student_career_preference(session, student_id)


@router.get("/{student_id}/class-transfer-history", response_model=list[StudentClassTransferHistoryItem])
def list_student_class_transfer_history(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> list[StudentClassTransferHistoryItem]:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.list_student_class_transfer_history(session, student_id)


@router.get("/{student_id}/teacher-comments", response_model=StudentTeacherCommentListResponse)
def list_student_teacher_comments(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> StudentTeacherCommentListResponse:
    return service.list_student_teacher_comments(
        session,
        student_id,
        actor=current_user,
        scope_class_ids=_scope_class_ids(current_user),
    )


@router.post("/{student_id}/teacher-comments", response_model=StudentTeacherCommentRead)
def create_student_teacher_comment(
    student_id: int,
    payload: StudentTeacherCommentPayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentTeacherCommentRead:
    return service.create_student_teacher_comment(
        session,
        student_id,
        payload,
        actor=current_user,
        scope_class_ids=_scope_class_ids(current_user),
    )


@router.post("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead)
def create_student_career_preference(
    student_id: int,
    payload: StudentCareerPreferencePayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.create_student_career_preference(session, student_id, payload)


@router.put("/{student_id}/career-preference", response_model=StudentCareerPreferenceRead)
def update_student_career_preference(
    student_id: int,
    payload: StudentCareerPreferencePayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentCareerPreferenceRead:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.update_student_career_preference(session, student_id, payload)


@router.get("/{student_id}/attachments", response_model=list[StudentAttachmentSummary])
def list_student_attachments(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> list[StudentAttachmentSummary]:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.list_student_attachments(session, student_id)


@router.post("/{student_id}/attachments", response_model=StudentAttachmentSummary)
def create_student_attachment(
    student_id: int,
    payload: StudentAttachmentPayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentAttachmentSummary:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.create_student_attachment(session, student_id, payload)


@router.delete("/{student_id}/attachments/{attachment_id}")
def delete_student_attachment(
    student_id: int,
    attachment_id: int,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))
    return service.delete_student_attachment(session, student_id, attachment_id)


@router.get("/{student_id}", response_model=StudentRead)
def get_student_detail(
    student_id: int,
    current_user: AuthContext = Depends(require_permission("students:read")),
    session: Session = Depends(get_db_session),
) -> StudentRead:
    return service.get_student_detail(session, student_id, scope_class_ids=_scope_class_ids(current_user))


@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentPayload,
    current_user: AuthContext = Depends(require_permission("students:write")),
    session: Session = Depends(get_db_session),
) -> StudentRead:
    return service.update_student(
        session,
        student_id,
        payload,
        scope_class_ids=_scope_class_ids(current_user),
        actor=current_user,
    )
