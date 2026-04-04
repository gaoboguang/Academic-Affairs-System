from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
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
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    current_grade = relationship("Grade")
    current_class = relationship("SchoolClass")
    guardians = relationship("StudentGuardian", back_populates="student", cascade="all, delete-orphan")
    class_histories = relationship(
        "StudentClassHistory", back_populates="student", cascade="all, delete-orphan"
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
