from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class Student(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student"

    student_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    admission_year: Mapped[int | None] = mapped_column(nullable=True)
    current_grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    current_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    student_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    art_track: Mapped[str | None] = mapped_column(String(50), nullable=True)
    origin_province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    current_grade = relationship("Grade")
    current_class = relationship("SchoolClass")
    guardians = relationship("StudentGuardian", back_populates="student", cascade="all, delete-orphan")
    class_histories = relationship(
        "StudentClassHistory", back_populates="student", cascade="all, delete-orphan"
    )
    career_preference = relationship(
        "StudentCareerPreference",
        back_populates="student",
        cascade="all, delete-orphan",
        uselist=False,
    )
    attachments = relationship(
        "StudentAttachment", back_populates="student", cascade="all, delete-orphan"
    )


class StudentGuardian(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_guardian"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    work_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)

    student = relationship("Student", back_populates="guardians")


class StudentClassHistory(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_class_history"
    __table_args__ = (
        UniqueConstraint("student_id", "class_id", "start_date", name="uq_student_class_history"),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    student = relationship("Student", back_populates="class_histories")


class StudentTeacherComment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_teacher_comment"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subject.id"), nullable=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    semester_id: Mapped[int | None] = mapped_column(ForeignKey("semester.id"), nullable=True)
    commented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    student = relationship("Student")
    teacher = relationship("Teacher")
    subject = relationship("Subject")
    school_class = relationship("SchoolClass")
    semester = relationship("Semester")


class StudentClassTransferBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_class_transfer_batch"

    source_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    target_class_id: Mapped[int] = mapped_column(ForeignKey("school_class.id"), nullable=False)
    target_grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    effective_on: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    requested_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    blocked_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    confirm_text: Mapped[str | None] = mapped_column(String(80), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    source_class = relationship("SchoolClass", foreign_keys=[source_class_id])
    target_class = relationship("SchoolClass", foreign_keys=[target_class_id])
    target_grade = relationship("Grade", foreign_keys=[target_grade_id])
    items = relationship(
        "StudentClassTransferItem",
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class StudentClassTransferItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_class_transfer_item"

    batch_id: Mapped[int] = mapped_column(ForeignKey("student_class_transfer_batch.id"), nullable=False)
    requested_student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("student.id"), nullable=True)
    student_no_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    student_name_snapshot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    from_grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    from_grade_name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    from_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    from_class_name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    to_grade_name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    to_class_name_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    before_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch = relationship("StudentClassTransferBatch", back_populates="items")
    student = relationship("Student", foreign_keys=[student_id])
    from_grade = relationship("Grade", foreign_keys=[from_grade_id])
    from_class = relationship("SchoolClass", foreign_keys=[from_class_id])
    to_grade = relationship("Grade", foreign_keys=[to_grade_id])
    to_class = relationship("SchoolClass", foreign_keys=[to_class_id])


class StudentAttachment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_attachment"
    __table_args__ = (
        UniqueConstraint("student_id", "stored_file_id", name="uq_student_attachment_file"),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_file.id"), nullable=False)
    attachment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student", back_populates="attachments")
    stored_file = relationship("StoredFile")


class StudentCareerPreference(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_career_preference"
    __table_args__ = (UniqueConstraint("student_id", name="uq_student_career_preference_student"),)

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    primary_direction_id: Mapped[int | None] = mapped_column(ForeignKey("employment_direction.id"), nullable=True)
    secondary_direction_id: Mapped[int | None] = mapped_column(ForeignKey("employment_direction.id"), nullable=True)
    alternative_direction_id: Mapped[int | None] = mapped_column(ForeignKey("employment_direction.id"), nullable=True)
    priority_focuses_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    preferred_industries_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    preferred_job_types_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    target_employment_cities_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    accepts_postgraduate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepts_public_service: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepts_certificate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepts_long_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    student = relationship("Student", back_populates="career_preference")
    primary_direction = relationship("EmploymentDirection", foreign_keys=[primary_direction_id])
    secondary_direction = relationship("EmploymentDirection", foreign_keys=[secondary_direction_id])
    alternative_direction = relationship("EmploymentDirection", foreign_keys=[alternative_direction_id])
