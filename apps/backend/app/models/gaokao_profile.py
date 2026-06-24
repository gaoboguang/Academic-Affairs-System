from __future__ import annotations

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class CollegeProfileDetail(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college_profile_detail"
    __table_args__ = (UniqueConstraint("college_id", name="uq_college_profile_detail_college"),)

    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    enrollment_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    authority_department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_985: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_211: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dual_class: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ruanke_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eol_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    master_program_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doctor_program_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    official_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admission_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    college = relationship("College")


class CollegeYearSummary(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college_year_summary"
    __table_args__ = (
        UniqueConstraint("college_id", "province", "year", name="uq_college_year_summary_core"),
    )

    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_plan_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    specialty_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_min_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    college = relationship("College")


class MajorProfileDetail(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "major_profile_detail"
    __table_args__ = (UniqueConstraint("major_id", name="uq_major_profile_detail_major"),)

    major_id: Mapped[int] = mapped_column(ForeignKey("major.id"), nullable=False)
    major_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    schooling_years: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    major = relationship("Major")


class CollegeMajorProfile(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college_major_profile"
    __table_args__ = (
        UniqueConstraint("college_id", "major_id", name="uq_college_major_profile_core"),
    )

    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    major_id: Mapped[int] = mapped_column(ForeignKey("major.id"), nullable=False)
    school_major_feature: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_national_feature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_provincial_feature: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_key_major: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schooling_years: Mapped[str | None] = mapped_column(String(50), nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    college = relationship("College")
    major = relationship("Major")
