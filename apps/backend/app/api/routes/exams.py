from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings, require_admin, require_permission
from app.core.config import Settings
from app.schemas.exam import (
    ExamListResponse,
    ExamPayload,
    ExamRead,
    ExamSubjectPayload,
    ExamSubjectRead,
    ScoreClassMappingPayload,
    ScoreImportPreviewResponse,
    ScoreImportProfileRead,
    ScoreQuestionImportResponse,
    ScoreImportResponse,
    ScoreRankAuditResponse,
    ScoreRebuildResponse,
    ScoreTargetLinePayload,
    ScoreTargetLineRead,
)
from app.services import exams as service
from app.services.auth import AuthContext

router = APIRouter(prefix="/exams", tags=["exams"])


def _scope_class_ids(current_user: AuthContext) -> set[int] | None:
    if current_user.is_admin:
        return None
    return set(current_user.class_scope_ids)


@router.get("", response_model=ExamListResponse)
def list_exams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    name: str | None = None,
    semester_id: int | None = None,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> ExamListResponse:
    return service.list_exams(
        session,
        page=page,
        page_size=page_size,
        name=name,
        semester_id=semester_id,
    )


@router.post("", response_model=ExamRead)
def create_exam(
    payload: ExamPayload,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> ExamRead:
    return service.create_exam(session, payload)


@router.get("/score-import-profiles", response_model=list[ScoreImportProfileRead])
def list_score_import_profiles(
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> list[ScoreImportProfileRead]:
    return service.list_score_import_profiles(session)


@router.get("/{exam_id}", response_model=ExamRead)
def get_exam_detail(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> ExamRead:
    return service.get_exam_detail(session, exam_id)


@router.put("/{exam_id}", response_model=ExamRead)
def update_exam(
    exam_id: int,
    payload: ExamPayload,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> ExamRead:
    return service.update_exam(session, exam_id, payload)


@router.get("/{exam_id}/subjects", response_model=list[ExamSubjectRead])
def list_exam_subjects(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> list[ExamSubjectRead]:
    return service.list_exam_subjects(session, exam_id)


@router.post("/{exam_id}/subjects", response_model=list[ExamSubjectRead])
def replace_exam_subjects(
    exam_id: int,
    payload: list[ExamSubjectPayload],
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> list[ExamSubjectRead]:
    return service.replace_exam_subjects(session, exam_id, payload)


@router.post("/{exam_id}/scores/import", response_model=ScoreImportResponse)
async def import_scores(
    exam_id: int,
    file: UploadFile = File(...),
    strategy: str = Form(default="overwrite"),
    rebuild: bool = Form(default=True),
    mapping_json: str | None = Form(default=None),
    profile_id: int | None = Form(default=None),
    save_profile_name: str | None = Form(default=None),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    current_user: AuthContext = Depends(require_permission("scores:import")),
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
        mapping_json=mapping_json,
        profile_id=profile_id,
        save_profile_name=save_profile_name,
        scope_class_ids=_scope_class_ids(current_user),
        actor=current_user,
    )


@router.post("/{exam_id}/scores/import/preview", response_model=ScoreImportPreviewResponse)
async def preview_score_import(
    exam_id: int,
    file: UploadFile = File(...),
    mapping_json: str | None = Form(default=None),
    profile_id: int | None = Form(default=None),
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> ScoreImportPreviewResponse:
    content = await file.read()
    return service.preview_score_import(
        session,
        exam_id=exam_id,
        filename=file.filename,
        content=content,
        mapping_json=mapping_json,
        profile_id=profile_id,
    )


@router.post("/{exam_id}/score-questions/import", response_model=ScoreQuestionImportResponse)
async def import_score_questions(
    exam_id: int,
    file: UploadFile = File(...),
    strategy: str = Form(default="overwrite"),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _current_user: AuthContext = Depends(require_admin),
) -> ScoreQuestionImportResponse:
    content = await file.read()
    return service.import_score_questions(
        session,
        settings,
        exam_id=exam_id,
        filename=file.filename,
        content=content,
        strategy=strategy,
    )


@router.post("/{exam_id}/rebuild")
def rebuild_exam(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> dict[str, str]:
    return service.rebuild_exam(session, exam_id)


@router.post("/{exam_id}/scores/rebuild-snapshots", response_model=ScoreRebuildResponse)
def rebuild_exam_score_snapshots(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> ScoreRebuildResponse:
    return service.rebuild_exam_score_snapshots(session, exam_id)


@router.get("/{exam_id}/score-rank-audit", response_model=ScoreRankAuditResponse)
def get_score_rank_audit(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> ScoreRankAuditResponse:
    return service.get_score_rank_audit(session, exam_id)


@router.put("/{exam_id}/score-class-mappings", response_model=ScoreRankAuditResponse)
def save_score_class_mappings(
    exam_id: int,
    payload: list[ScoreClassMappingPayload],
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> ScoreRankAuditResponse:
    return service.save_score_class_mappings(session, exam_id, payload)


@router.get("/{exam_id}/score-target-lines", response_model=list[ScoreTargetLineRead])
def list_score_target_lines(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> list[ScoreTargetLineRead]:
    return service.list_score_target_lines(session, exam_id)


@router.put("/{exam_id}/score-target-lines", response_model=list[ScoreTargetLineRead])
def replace_score_target_lines(
    exam_id: int,
    payload: list[ScoreTargetLinePayload],
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_admin),
) -> list[ScoreTargetLineRead]:
    return service.replace_score_target_lines(session, exam_id, payload)


@router.get("/{exam_id}/score-batches")
def list_score_batches(
    exam_id: int,
    session: Session = Depends(get_db_session),
    _current_user: AuthContext = Depends(require_permission("scores:import")),
) -> list[dict]:
    return service.get_score_import_batches(session, exam_id)
