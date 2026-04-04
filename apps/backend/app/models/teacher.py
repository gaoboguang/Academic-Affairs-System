from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class Teacher(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "teacher"

    teacher_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subject.id"), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    title_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    position_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_head_teacher: Mapped[bool] = mapped_column(default=False, nullable=False)
    employment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject = relationship("Subject")
    teaching_assignments = relationship(
        "TeachingAssignment", back_populates="teacher", cascade="all, delete-orphan"
    )
    title_histories = relationship(
        "TeacherTitleHistory", back_populates="teacher", cascade="all, delete-orphan"
    )


class TeacherTitleHistory(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "teacher_title_history"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    title_code: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher = relationship("Teacher", back_populates="title_histories")


class TeachingAssignment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "teaching_assignment"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "semester_id",
            "class_id",
            "subject_id",
            "course_type",
            name="uq_teaching_assignment",
        ),
    )

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grade.id"), nullable=True)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subject.id"), nullable=True)
    course_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weekly_periods_manual: Mapped[int | None] = mapped_column(Integer, nullable=True)

    teacher = relationship("Teacher", back_populates="teaching_assignments")
    semester = relationship("Semester", back_populates="teaching_assignments")
    grade = relationship("Grade")
    school_class = relationship("SchoolClass")
    subject = relationship("Subject")


class ClassAdviserAssignment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "class_adviser_assignment"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("school_class.id"), nullable=False)
    semester_id: Mapped[int | None] = mapped_column(ForeignKey("semester.id"), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

