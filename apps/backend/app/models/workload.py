from __future__ import annotations

from datetime import datetime, time

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class TimetableBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "timetable_batch"

    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="processing", nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester = relationship("Semester")
    entries = relationship("TimetableEntry", back_populates="batch", cascade="all, delete-orphan")


class TimetableEntry(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "timetable_entry"

    batch_id: Mapped[int] = mapped_column(ForeignKey("timetable_batch.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    period_no: Mapped[int] = mapped_column(Integer, nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teacher.id"), nullable=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subject.id"), nullable=True)
    course_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    week_rule: Mapped[str] = mapped_column(String(30), default="all", nullable=False)
    week_list_json: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(30), default="matched", nullable=False)
    raw_teacher_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_class_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_subject_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_course_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    batch = relationship("TimetableBatch", back_populates="entries")
    semester = relationship("Semester")
    teacher = relationship("Teacher")
    school_class = relationship("SchoolClass")
    subject = relationship("Subject")


class PeriodDefinition(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "period_definition"
    __table_args__ = (UniqueConstraint("period_no", name="uq_period_definition_period_no"),)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    period_no: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    period_type: Mapped[str | None] = mapped_column(String(30), nullable=True)


class WorkloadRuleVersion(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "workload_rule_version"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    semester_id: Mapped[int | None] = mapped_column(ForeignKey("semester.id"), nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester = relationship("Semester")
    items = relationship("WorkloadRuleItem", back_populates="rule_version", cascade="all, delete-orphan")


class WorkloadRuleItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "workload_rule_item"

    rule_version_id: Mapped[int] = mapped_column(ForeignKey("workload_rule_version.id"), nullable=False)
    dimension_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_key: Mapped[str] = mapped_column(String(100), nullable=False)
    coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    fixed_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    rule_version = relationship("WorkloadRuleVersion", back_populates="items")


class TeacherWorkloadExtra(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "teacher_workload_extra"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    coefficient: Mapped[float] = mapped_column(Float, default=1, nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher = relationship("Teacher")
    semester = relationship("Semester")


class TeacherWorkloadResult(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "teacher_workload_result"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "semester_id",
            "rule_version_id",
            name="uq_teacher_workload_result",
        ),
    )

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    rule_version_id: Mapped[int] = mapped_column(ForeignKey("workload_rule_version.id"), nullable=False)
    weekly_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    monthly_hours_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    semester_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    semester_workload: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )

    teacher = relationship("Teacher")
    semester = relationship("Semester")
    rule_version = relationship("WorkloadRuleVersion")

