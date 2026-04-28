from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class AttendanceRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "attendance_record"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "record_date",
            "scope",
            "period_index",
            name="uq_attendance_record_student_date_scope_period",
        ),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="day", nullable=False)
    period_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_job.id"), nullable=True)

    student = relationship("Student")
    source_batch = relationship("ImportJob")


class BehaviorRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "behavior_record"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="中", nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    handler_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    points_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    attachment_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_job.id"), nullable=True)

    student = relationship("Student")
    source_batch = relationship("ImportJob")
