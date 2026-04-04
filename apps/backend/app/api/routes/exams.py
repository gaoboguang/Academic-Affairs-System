from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.exam import ExamListResponse, ExamPayload, ExamRead, ExamSubjectPayload, ExamSubjectRead, ScoreImportResponse
from app.services import exams as service

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=ExamListResponse)
def list_exams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    name: str | None = None,
    semester_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> ExamListResponse:
    return service.list_exams(
        session,
        page=page,
        page_size=page_size,
        name=name,
        semester_id=semester_id,
    )


@router.post("", response_model=ExamRead)
def create_exam(payload: ExamPayload, session: Session = Depends(get_db_session)) -> ExamRead:
    return service.create_exam(session, payload)


@router.get("/{exam_id}", response_model=ExamRead)
def get_exam_detail(exam_id: int, session: Session = Depends(get_db_session)) -> ExamRead:
    return service.get_exam_detail(session, exam_id)


@router.put("/{exam_id}", response_model=ExamRead)
def update_exam(
    exam_id: int,
    payload: ExamPayload,
    session: Session = Depends(get_db_session),
) -> ExamRead:
    return service.update_exam(session, exam_id, payload)


@router.get("/{exam_id}/subjects", response_model=list[ExamSubjectRead])
def list_exam_subjects(exam_id: int, session: Session = Depends(get_db_session)) -> list[ExamSubjectRead]:
    return service.list_exam_subjects(session, exam_id)


@router.post("/{exam_id}/subjects", response_model=list[ExamSubjectRead])
def replace_exam_subjects(
    exam_id: int,
    payload: list[ExamSubjectPayload],
    session: Session = Depends(get_db_session),
) -> list[ExamSubjectRead]:
    return service.replace_exam_subjects(session, exam_id, payload)


@router.post("/{exam_id}/scores/import", response_model=ScoreImportResponse)
async def import_scores(
    exam_id: int,
    file: UploadFile = File(...),
    strategy: str = Form(default="overwrite"),
    rebuild: bool = Form(default=True),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ScoreImportResponse:
    content = await file.read()
    return service.import_scores(
        session,
        settings,
        exam_id=exam_id,
        filename=file.filename,
        content=content,
        strategy=strategy,
        rebuild=rebuild,
    )


@router.post("/{exam_id}/rebuild")
def rebuild_exam(exam_id: int, session: Session = Depends(get_db_session)) -> dict[str, str]:
    return service.rebuild_exam(session, exam_id)


@router.get("/{exam_id}/score-batches")
def list_score_batches(exam_id: int, session: Session = Depends(get_db_session)) -> list[dict]:
    return service.get_score_import_batches(session, exam_id)

