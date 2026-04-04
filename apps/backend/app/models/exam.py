from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class Exam(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "exam"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    grade_scope_json: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    is_trend_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester = relationship("Semester")
    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")
    score_records = relationship("ScoreRecord", back_populates="exam", cascade="all, delete-orphan")


class ExamSubject(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "exam_subject"
    __table_args__ = (UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    full_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_in_total: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    excellent_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exam = relationship("Exam", back_populates="subjects")
    subject = relationship("Subject")


class ScoreImportBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_import_batch"

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processing", nullable=False)
    error_report_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    exam = relationship("Exam")
    records = relationship("ScoreRecord", back_populates="import_batch")


class ScoreRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_record"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_record"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_status: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    raw_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("score_import_batch.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam", back_populates="score_records")
    student = relationship("Student")
    subject = relationship("Subject")
    import_batch = relationship("ScoreImportBatch", back_populates="records")


class ScoreTotalSnapshot(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_total_snapshot"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_score_total_snapshot"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_mode: Mapped[str] = mapped_column(String(30), default="competition", nullable=False)
    rebuilt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )

    exam = relationship("Exam")
    student = relationship("Student")


class ScoreSubjectSnapshot(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_subject_snapshot"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_subject_snapshot"),
    )

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    excellent_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pass_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    exam = relationship("Exam")
    student = relationship("Student")
    subject = relationship("Subject")

