from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.analytics.scores import calculate_rate, safe_mean
from app.core.config import Settings
from app.models import AttendanceRecord, BackupRecord, BehaviorRecord, Exam, Grade, SchoolClass, ScoreRecord, Student, Teacher, TeachingAssignment
from app.repositories.exams import get_subject_snapshots_for_exam, get_total_snapshots_for_exam
from app.repositories.system import list_backups, list_recent_import_jobs
from app.schemas.dashboard import (
    DashboardBackupSummary,
    DashboardDataHealthSummary,
    DashboardImportJob,
    DashboardRecentExamSummary,
    DashboardSummary,
)
from app.services.data_quality import build_data_quality_issues
from app.services.planning import build_dashboard_planning_summary
from app.utils.data_health import build_data_health_report


def get_dashboard_summary(session: Session, settings: Settings) -> DashboardSummary:
    latest_backup = _get_latest_backup(session, settings)
    latest_backup_time = latest_backup.created_at.isoformat() if latest_backup and latest_backup.created_at else None

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
    data_health = _build_data_health_summary(session, settings)
    planning_summary = build_dashboard_planning_summary(session)

    return DashboardSummary(
        student_total=session.scalar(select(func.count()).select_from(Student)) or 0,
        teacher_total=session.scalar(select(func.count()).select_from(Teacher)) or 0,
        exam_total=session.scalar(select(func.count()).select_from(Exam)) or 0,
        score_record_total=session.scalar(select(func.count()).select_from(ScoreRecord)) or 0,
        grade_total=session.scalar(select(func.count()).select_from(Grade)) or 0,
        class_total=session.scalar(select(func.count()).select_from(SchoolClass)) or 0,
        recent_imports=recent_imports,
        latest_backup_time=latest_backup_time,
        latest_backup=latest_backup,
        recent_exam=recent_exam,
        data_health=data_health,
        data_quality_issues=data_quality_issues,
        planning_summary=planning_summary,
    )


def _get_latest_backup(session: Session, settings: Settings) -> DashboardBackupSummary | None:
    backup_records = list_backups(session)
    if backup_records:
        record = backup_records[0]
        return _serialize_backup_record(record)

    backup_files = sorted(settings.backups_dir.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not backup_files:
        return None

    latest_file = backup_files[0]
    return DashboardBackupSummary(
        backup_name=latest_file.name,
        created_at=None,
        status="success",
        file_size=latest_file.stat().st_size,
    )


def _serialize_backup_record(record: BackupRecord) -> DashboardBackupSummary:
    return DashboardBackupSummary(
        backup_name=record.backup_name,
        created_at=record.created_at,
        status=record.status,
        file_size=record.file_size,
    )


def _build_data_health_summary(session: Session, settings: Settings) -> DashboardDataHealthSummary:
    report = build_data_health_report(settings.db_path)
    delivery = report.get("delivery_assessment") or {}
    gaps = [
        *_build_local_academic_gaps(session),
        *list(report.get("gaps") or []),
    ]
    warning_items = list(delivery.get("warning_items") or [])
    blocking_items = list(delivery.get("blocking_items") or [])

    return DashboardDataHealthSummary(
        status=str(delivery.get("status") or ("warning" if gaps else "pass")),
        label=str(delivery.get("label") or ("有数据警告" if gaps else "P0 可通过")),
        summary=str(delivery.get("summary") or report.get("summary") or ""),
        p0_gap_count=len(gaps),
        warning_count=len(warning_items),
        blocking_count=len(blocking_items),
        gaps=gaps[:4],
    )


def _build_local_academic_gaps(session: Session) -> list[str]:
    gaps: list[str] = []
    if (session.scalar(select(func.count()).select_from(ScoreRecord)) or 0) == 0:
        gaps.append("教务成绩数据缺口：尚未导入成绩记录。")
    if (session.scalar(select(func.count()).select_from(AttendanceRecord)) or 0) == 0:
        gaps.append("教务考勤数据缺口：尚未导入考勤记录。")
    if (session.scalar(select(func.count()).select_from(BehaviorRecord)) or 0) == 0:
        gaps.append("教务行为数据缺口：尚未导入行为记录。")
    if (session.scalar(select(func.count()).select_from(TeachingAssignment)) or 0) == 0:
        gaps.append("教务任教关系缺口：尚未维护任教关系。")
    if not list_backups(session):
        gaps.append("本地备份缺口：尚未创建可恢复的本地备份。")
    return gaps


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
