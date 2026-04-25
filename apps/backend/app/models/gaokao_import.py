from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class GaokaoSourceDocument(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "gaokao_source_document"
    __table_args__ = (
        UniqueConstraint(
            "province",
            "year",
            "source_type",
            "url",
            name="uq_gaokao_source_document_url",
        ),
    )

    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    official_org: Mapped[str] = mapped_column(String(150), nullable=False)
    source_registry_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published_at: Mapped[date | None] = mapped_column(nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    local_file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parser_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="registered", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    import_runs = relationship("GaokaoImportRun", back_populates="source_document", cascade="all, delete-orphan")


class GaokaoImportRun(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "gaokao_import_run"

    source_document_id: Mapped[int] = mapped_column(ForeignKey("gaokao_source_document.id"), nullable=False)
    importer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_snapshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_document = relationship("GaokaoSourceDocument", back_populates="import_runs")
