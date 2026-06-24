from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class ConfigItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "config_item"
    __table_args__ = (
        UniqueConstraint("config_group", "config_key", name="uq_config_group_key"),
    )

    config_group: Mapped[str] = mapped_column(String(50), nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(30), default="string", nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ImportJob(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "import_job"

    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AuditLog(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "audit_log"

    module: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("app_user.id"), nullable=True)
    actor_username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(80), nullable=True)
    detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class StoredFile(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "stored_file"

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)


class BackupRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "backup_record"

    backup_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)


class ReportExportRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "report_export_record"

    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_name: Mapped[str] = mapped_column(String(100), nullable=False)
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    exported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
