from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class AcademicYear(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "academic_year"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)

    semesters = relationship("Semester", back_populates="academic_year")


class Semester(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "semester"
    __table_args__ = (UniqueConstraint("academic_year_id", "name", name="uq_semester_year_name"),)

    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_year.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    week_count: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)

    academic_year = relationship("AcademicYear", back_populates="semesters")
    teaching_assignments = relationship("TeachingAssignment", back_populates="semester")


class Grade(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "grade"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    classes = relationship("SchoolClass", back_populates="grade")


class SchoolClass(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "school_class"
    __table_args__ = (UniqueConstraint("grade_id", "name", name="uq_class_grade_name"),)

    grade_id: Mapped[int] = mapped_column(ForeignKey("grade.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    class_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    head_teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teacher.id"), nullable=True)
    student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    grade = relationship("Grade", back_populates="classes")
    head_teacher = relationship("Teacher", foreign_keys=[head_teacher_id])


class Subject(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "subject"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="academic", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_in_total_default: Mapped[bool] = mapped_column(default=True, nullable=False)


class DictType(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "dict_type"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    items = relationship("DictItem", back_populates="dict_type")


class DictItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "dict_item"
    __table_args__ = (UniqueConstraint("dict_type_id", "code", name="uq_dict_item_code"),)

    dict_type_id: Mapped[int] = mapped_column(ForeignKey("dict_type.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    dict_type = relationship("DictType", back_populates="items")

