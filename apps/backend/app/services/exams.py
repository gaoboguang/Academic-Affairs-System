from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.scores import rebuild_exam_snapshots
from app.core.config import Settings
from app.importers.scores import ScoreImporter
from app.models import ConfigItem, Exam, ExamSubject, Grade, ScoreImportBatch, Semester, Subject
from app.repositories.exams import get_exam, list_exam_subjects as repo_list_exam_subjects, list_exams as repo_list_exams, list_score_batches
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.exam import (
    ExamListResponse,
    ExamPayload,
    ExamRead,
    ExamSubjectPayload,
    ExamSubjectRead,
    ScoreImportResponse,
)
def _serialize_exam_with_grade_map(item: Exam, grade_map: dict[int, str]) -> ExamRead:
    semester_name = None
    if item.semester and item.semester.academic_year:
        semester_name = f"{item.semester.academic_year.name} {item.semester.name}"
    elif item.semester:
        semester_name = item.semester.name
    grade_scope_names = [grade_map.get(grade_id, str(grade_id)) for grade_id in (item.grade_scope_json or [])]
    return ExamRead(
        id=item.id,
        name=item.name,
        exam_type=item.exam_type,
        exam_date=item.exam_date,
        semester_id=item.semester_id,
        semester_name=semester_name,
        grade_scope_json=item.grade_scope_json,
        grade_scope_names=grade_scope_names,
        is_trend_enabled=item.is_trend_enabled,
        status=item.status,
        note=item.note,
        is_active=item.is_active,
        subject_count=len([subject for subject in item.subjects if subject.is_active]),
    )


def _serialize_exam_subject(item: ExamSubject) -> ExamSubjectRead:
    return ExamSubjectRead(
        id=item.id,
        exam_id=item.exam_id,
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        full_score=item.full_score,
        is_in_total=item.is_in_total,
        excellent_line=item.excellent_line,
        pass_line=item.pass_line,
        sort_order=item.sort_order,
        is_active=item.is_active,
    )


def _get_rank_mode(session: Session) -> str:
    config = session.scalar(
        select(ConfigItem).where(
            ConfigItem.config_group == "analytics",
            ConfigItem.config_key == "ranking_mode",
        )
    )
    return config.config_value if config else "competition"


def list_exams(
    session: Session,
    *,
    page: int,
    page_size: int,
    name: str | None = None,
    semester_id: int | None = None,
) -> ExamListResponse:
    items, total = repo_list_exams(session, page=page, page_size=page_size, name=name, semester_id=semester_id)
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return ExamListResponse(
        items=[_serialize_exam_with_grade_map(item, grade_map) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_exam_detail(session: Session, exam_id: int) -> ExamRead:
    item = get_exam(session, exam_id)
    if not item:
        raise HTTPException(status_code=404, detail="考试不存在")
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def create_exam(session: Session, payload: ExamPayload) -> ExamRead:
    _validate_exam_payload(session, payload)
    item = Exam(**payload.model_dump())
    session.add(item)
    session.flush()
    write_audit_log(session, module="exams", action="create", target_type="exam", target_id=str(item.id))
    item = get_exam(session, item.id) or item
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def update_exam(session: Session, exam_id: int, payload: ExamPayload) -> ExamRead:
    item = get_exam(session, exam_id)
    if not item:
        raise HTTPException(status_code=404, detail="考试不存在")
    _validate_exam_payload(session, payload)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.flush()
    write_audit_log(session, module="exams", action="update", target_type="exam", target_id=str(item.id))
    session.refresh(item)
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def _validate_exam_payload(session: Session, payload: ExamPayload) -> None:
    semester = session.get(Semester, payload.semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.grade_scope_json:
        valid_ids = {grade.id for grade in session.scalars(select(Grade)).all()}
        invalid = [grade_id for grade_id in payload.grade_scope_json if grade_id not in valid_ids]
        if invalid:
            raise HTTPException(status_code=400, detail=f"年级范围无效: {invalid}")


def list_exam_subjects(session: Session, exam_id: int) -> list[ExamSubjectRead]:
    if not get_exam(session, exam_id):
        raise HTTPException(status_code=404, detail="考试不存在")
    return [_serialize_exam_subject(item) for item in repo_list_exam_subjects(session, exam_id)]


def replace_exam_subjects(
    session: Session,
    exam_id: int,
    payload: list[ExamSubjectPayload],
) -> list[ExamSubjectRead]:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    subject_ids = [item.subject_id for item in payload]
    if len(subject_ids) != len(set(subject_ids)):
        raise HTTPException(status_code=400, detail="考试科目重复")
    for item in payload:
        if not session.get(Subject, item.subject_id):
            raise HTTPException(status_code=404, detail=f"学科不存在: {item.subject_id}")

    existing = list(repo_list_exam_subjects(session, exam_id))
    existing_map = {item.subject_id: item for item in existing}
    keep_ids = set(subject_ids)
    for subject_id, current in existing_map.items():
        if subject_id not in keep_ids:
            current.is_active = False
    for item in payload:
        current = existing_map.get(item.subject_id)
        if current:
            for key, value in item.model_dump().items():
                setattr(current, key, value)
            current.is_active = True
        else:
            session.add(ExamSubject(exam_id=exam_id, **item.model_dump()))
    session.flush()
    write_audit_log(session, module="exams", action="replace_subjects", target_type="exam", target_id=str(exam_id))
    return [_serialize_exam_subject(item) for item in repo_list_exam_subjects(session, exam_id)]


def rebuild_exam(session: Session, exam_id: int) -> dict[str, str]:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    rank_mode = _get_rank_mode(session)
    rebuild_exam_snapshots(session, exam, rank_mode)
    write_audit_log(session, module="exams", action="rebuild", target_type="exam", target_id=str(exam.id))
    return {"message": "统计快照已重建"}


def import_scores(
    session: Session,
    settings: Settings,
    *,
    exam_id: int,
    filename: str | None,
    content: bytes,
    strategy: str,
    rebuild: bool = True,
) -> ScoreImportResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not repo_list_exam_subjects(session, exam_id):
        raise HTTPException(status_code=400, detail="请先配置考试科目")

    batch = ScoreImportBatch(exam_id=exam_id, source_filename=filename, import_time=datetime.now())
    session.add(batch)
    session.flush()
    job = create_import_job(session, "scores", filename)
    job.started_at = datetime.now()

    importer = ScoreImporter(session, settings, exam)
    try:
        result = importer.execute(filename=filename, content=content, strategy=strategy, batch=batch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    batch.total_rows = result.total_rows
    batch.success_rows = result.success_rows
    batch.failed_rows = result.failed_rows
    batch.status = "success" if result.failed_rows == 0 else "partial_success"
    batch.error_report_path = result.error_report_path

    if rebuild:
        rebuild_exam_snapshots(session, exam, _get_rank_mode(session))

    job.finished_at = datetime.now()
    job.status = batch.status
    job.result_json = {"exam_id": exam_id, "batch_id": batch.id, **result.model_dump()}
    write_audit_log(
        session,
        module="exams",
        action="import_scores",
        target_type="score_import_batch",
        target_id=str(batch.id),
        detail_json=job.result_json,
    )
    return ScoreImportResponse(batch_id=batch.id, **result.model_dump())


def get_score_import_batches(session: Session, exam_id: int) -> list[dict]:
    if not get_exam(session, exam_id):
        raise HTTPException(status_code=404, detail="考试不存在")
    return [
        {
            "id": item.id,
            "source_filename": item.source_filename,
            "import_time": item.import_time.isoformat(sep=" ", timespec="seconds"),
            "total_rows": item.total_rows,
            "success_rows": item.success_rows,
            "failed_rows": item.failed_rows,
            "status": item.status,
            "error_report_path": item.error_report_path,
        }
        for item in list_score_batches(session, exam_id)
    ]
