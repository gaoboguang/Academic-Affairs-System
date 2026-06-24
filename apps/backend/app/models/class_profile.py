from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class ClassHonor(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "class_honor"
    __table_args__ = (UniqueConstraint("class_id", "title", "awarded_on", name="uq_class_honor_class_title_date"),)

    class_id: Mapped[int] = mapped_column(ForeignKey("school_class.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    honor_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    awarded_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(150), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    school_class = relationship("SchoolClass")
