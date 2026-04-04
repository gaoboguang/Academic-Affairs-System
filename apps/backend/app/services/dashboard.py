from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.analytics.scores import calculate_rate, safe_mean
from app.core.config import Settings
from app.models import Exam, Grade, SchoolClass, Student, Teacher
from app.repositories.exams import get_subject_snapshots_for_exam, get_total_snapshots_for_exam
from app.repositories.system import list_recent_import_jobs
from app.schemas.dashboard import DashboardImportJob, DashboardRecentExamSummary, DashboardSummary
from app.services.data_quality import build_data_quality_issues


def get_dashboard_summary(session: Session, settings: Settings) -> DashboardSummary:
    latest_backup = None
    backups = sorted(settings.backups_dir.glob("*.zip"))
    if backups:
        latest_backup = backups[-1].name

    recent_imports = [
        DashboardImportJob(
            id=item.id,
            job_type=item.job_type,
            source_filename=item.source_filename,
            status=item.status,
            started_at=item.started_at,
            finished_at=item.finished_at,
        )
        for item in list_recent_import_jobs(session)
    ]
    recent_exam = _build_recent_exam_summary(session)
    data_quality_issues = build_data_quality_issues(session, limit=4)

    return DashboardSummary(
        student_total=session.scalar(select(func.count()).select_from(Student)) or 0,
        teacher_total=session.scalar(select(func.count()).select_from(Teacher)) or 0,
        grade_total=session.scalar(select(func.count()).select_from(Grade)) or 0,
        class_total=session.scalar(select(func.count()).select_from(SchoolClass)) or 0,
        recent_imports=recent_imports,
        latest_backup_time=latest_backup,
        recent_exam=recent_exam,
        data_quality_issues=data_quality_issues,
    )


def _build_recent_exam_summary(session: Session) -> DashboardRecentExamSummary | None:
    exam = session.scalar(
        select(Exam)
        .options(selectinload(Exam.subjects))
        .where(Exam.is_active.is_(True))
        .order_by(Exam.exam_date.desc(), Exam.id.desc())
    )
    if not exam:
        return None

    total_snapshots = list(get_total_snapshots_for_exam(session, exam.id))
    participant_count = len(total_snapshots)
    average_score = safe_mean([item.total_score for item in total_snapshots]) if total_snapshots else None
    excellent_rate = _calculate_exam_excellent_rate(session, exam.id, exam.subjects, total_snapshots)
    return DashboardRecentExamSummary(
        exam_id=exam.id,
        exam_name=exam.name,
        exam_date=exam.exam_date,
        participant_count=participant_count,
        average_score=average_score,
        excellent_rate=excellent_rate,
    )


def _calculate_exam_excellent_rate(session: Session, exam_id: int, subjects, total_snapshots) -> float | None:
    in_total_subjects = [item for item in subjects if item.is_active and item.is_in_total]
    if total_snapshots and in_total_subjects and all(item.excellent_line is not None for item in in_total_subjects):
        threshold = sum(float(item.excellent_line or 0) for item in in_total_subjects)
        return calculate_rate(
            sum(1 for item in total_snapshots if item.total_score >= threshold),
            len(total_snapshots),
        )

    subject_snapshots = get_subject_snapshots_for_exam(session, exam_id)
    grouped: dict[int, list] = defaultdict(list)
    for item in subject_snapshots:
        if item.score is None:
            continue
        grouped[item.subject_id].append(item)
    rates = [
        calculate_rate(sum(1 for item in items if item.excellent_flag), len(items))
        for items in grouped.values()
        if items
    ]
    if not rates:
        return None
    return round(sum(rates) / len(rates), 2)
