from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class College(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    college_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    school_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    school_level_tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    supports_art: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    aliases = relationship("CollegeAlias", back_populates="college", cascade="all, delete-orphan")
    majors = relationship("CollegeMajor", back_populates="college", cascade="all, delete-orphan")


class CollegeAlias(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college_alias"
    __table_args__ = (UniqueConstraint("college_id", "alias_name", name="uq_college_alias_name"),)

    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(150), nullable=False)

    college = relationship("College", back_populates="aliases")


class Major(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "major"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    major_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(150), nullable=True)
    career_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_art_related: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    colleges = relationship("CollegeMajor", back_populates="major", cascade="all, delete-orphan")


class CollegeMajor(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "college_major"
    __table_args__ = (UniqueConstraint("college_id", "major_id", name="uq_college_major"),)

    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    major_id: Mapped[int] = mapped_column(ForeignKey("major.id"), nullable=False)
    enrollment_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    college = relationship("College", back_populates="majors")
    major = relationship("Major", back_populates="colleges")


class AdmissionRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "admission_record"
    __table_args__ = (
        UniqueConstraint(
            "year",
            "province",
            "batch",
            "college_id",
            "major_id",
            "student_type",
            "art_track",
            name="uq_admission_record_core",
        ),
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    batch: Mapped[str] = mapped_column(String(50), nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    major_id: Mapped[int | None] = mapped_column(ForeignKey("major.id"), nullable=True)
    student_type: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    art_track: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_requirement: Mapped[str | None] = mapped_column(String(100), nullable=True)
    min_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    plan_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    college = relationship("College")
    major = relationship("Major")


class RecommendationScheme(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "recommendation_scheme"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    student_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    results = relationship("RecommendationResult", back_populates="scheme", cascade="all, delete-orphan")


class RecommendationResult(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "recommendation_result"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("recommendation_scheme.id"), nullable=False)
    result_type: Mapped[str] = mapped_column(String(20), nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    major_id: Mapped[int | None] = mapped_column(ForeignKey("major.id"), nullable=True)
    reference_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_basis: Mapped[str] = mapped_column(String(50), nullable=False)
    ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_flags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

    student = relationship("Student")
    exam = relationship("Exam")
    scheme = relationship("RecommendationScheme", back_populates="results")
    college = relationship("College")
    major = relationship("Major")
