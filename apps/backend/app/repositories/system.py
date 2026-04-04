from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AuditLog, BackupRecord, ImportJob, ReportExportRecord, StoredFile


def list_recent_import_jobs(session: Session, limit: int = 5) -> Sequence[ImportJob]:
    return session.scalars(
        select(ImportJob).order_by(desc(ImportJob.started_at), desc(ImportJob.id)).limit(limit)
    ).all()


def create_import_job(session: Session, job_type: str, source_filename: str | None) -> ImportJob:
    job = ImportJob(job_type=job_type, source_filename=source_filename, status="processing")
    session.add(job)
    session.flush()
    return job


def write_audit_log(
    session: Session,
    *,
    module: str,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    detail_json: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        module=module,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail_json=detail_json,
    )
    session.add(log)
    session.flush()
    return log


def list_audit_logs(session: Session, limit: int = 100) -> Sequence[AuditLog]:
    return session.scalars(
        select(AuditLog).order_by(desc(AuditLog.created_at), desc(AuditLog.id)).limit(limit)
    ).all()


def get_stored_file(session: Session, file_id: int) -> StoredFile | None:
    return session.get(StoredFile, file_id)


def list_backups(session: Session) -> Sequence[BackupRecord]:
    return session.scalars(
        select(BackupRecord).order_by(desc(BackupRecord.created_at), desc(BackupRecord.id))
    ).all()


def get_backup_record(session: Session, backup_id: int) -> BackupRecord | None:
    return session.get(BackupRecord, backup_id)


def list_report_exports(session: Session, limit: int = 100) -> Sequence[ReportExportRecord]:
    return session.scalars(
        select(ReportExportRecord).order_by(desc(ReportExportRecord.exported_at), desc(ReportExportRecord.id)).limit(limit)
    ).all()


def get_report_export(session: Session, export_id: int) -> ReportExportRecord | None:
    return session.get(ReportExportRecord, export_id)
