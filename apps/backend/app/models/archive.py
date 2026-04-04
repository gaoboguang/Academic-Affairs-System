from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class StudentGrowthRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_growth_record"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")
    attachments = relationship(
        "StudentGrowthAttachment",
        back_populates="record",
        cascade="all, delete-orphan",
    )


class StudentGrowthAttachment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_growth_attachment"

    record_id: Mapped[int] = mapped_column(ForeignKey("student_growth_record.id"), nullable=False)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_file.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    record = relationship("StudentGrowthRecord", back_populates="attachments")
    stored_file = relationship("StoredFile")
