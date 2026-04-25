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
    employment_mappings = relationship("MajorEmploymentMapping", back_populates="major", cascade="all, delete-orphan")


class EmploymentDirection(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "employment_direction"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alias_names_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_job_types_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    common_industries_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    prefers_postgraduate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_certificate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_long_cycle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_art: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    major_mappings = relationship("MajorEmploymentMapping", back_populates="direction", cascade="all, delete-orphan")


class MajorEmploymentMapping(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "major_employment_mapping"
    __table_args__ = (UniqueConstraint("major_id", "direction_id", name="uq_major_employment_mapping_core"),)

    major_id: Mapped[int] = mapped_column(ForeignKey("major.id"), nullable=False)
    direction_id: Mapped[int] = mapped_column(ForeignKey("employment_direction.id"), nullable=False)
    strength: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    recommendation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_postgraduate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_certificate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supported_student_types_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    supports_art: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    major = relationship("Major", back_populates="employment_mappings")
    direction = relationship("EmploymentDirection", back_populates="major_mappings")


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
    source_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    import_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    college = relationship("College")
    major = relationship("Major")


class EnrollmentPlan(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "enrollment_plan"
    __table_args__ = (
        UniqueConstraint(
            "year",
            "province",
            "batch",
            "exam_mode",
            "college_id",
            "major_group_code",
            "major_name_snapshot",
            "student_type",
            name="uq_enrollment_plan_core",
        ),
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    batch: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    college_id: Mapped[int] = mapped_column(ForeignKey("college.id"), nullable=False)
    major_id: Mapped[int | None] = mapped_column(ForeignKey("major.id"), nullable=True)
    college_code_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    major_group_code: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    major_name_snapshot: Mapped[str] = mapped_column(String(150), default="", nullable=False)
    major_code_snapshot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plan_count: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_requirement: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tuition_fee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    schooling_years: Mapped[str | None] = mapped_column(String(50), nullable=True)
    training_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    student_type: Mapped[str] = mapped_column(String(50), default="general", nullable=False)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_batch_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    import_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    college = relationship("College")
    major = relationship("Major")


class ProvinceVolunteerRule(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "province_volunteer_rule"
    __table_args__ = (
        UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "batch",
            "candidate_type",
            name="uq_province_volunteer_rule_core",
        ),
    )

    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    batch: Mapped[str] = mapped_column(String(50), nullable=False)
    candidate_type: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    batch_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, default=750, nullable=False)
    volunteer_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    volunteer_unit_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_requirement_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    required_subjects_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    first_choice_subjects_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reselect_subjects_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    score_rule_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    parallel_rule_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    max_major_per_unit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_parallel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_adjustment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    support_collect_round: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_rules_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProvinceScoreTransformRule(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "province_score_transform_rule"
    __table_args__ = (
        UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "subject_name",
            name="uq_province_score_transform_rule_core",
        ),
    )

    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    subject_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_name: Mapped[str] = mapped_column(String(50), nullable=False)
    score_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_table_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    formula_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SubjectRequirementDict(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "subject_requirement_dict"
    __table_args__ = (
        UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "requirement_code",
            name="uq_subject_requirement_dict_core",
        ),
    )

    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    requirement_code: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement_text: Mapped[str] = mapped_column(String(150), nullable=False)
    match_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    normalized_subjects_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SpecialTypeRule(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "special_type_rule"
    __table_args__ = (
        UniqueConstraint(
            "province",
            "year",
            "student_type",
            "category_code",
            name="uq_special_type_rule_core",
        ),
    )

    province: Mapped[str] = mapped_column(String(50), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    student_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category_code: Mapped[str] = mapped_column(String(100), nullable=False)
    category_label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_keywords_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    review_notes_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    priority_bonus: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority_notes_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class StudentGaokaoScoreProjection(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_gaokao_score_projection"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(50), default="山东", nullable=False)
    source_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_range_low: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_range_high: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_level: Mapped[str] = mapped_column(String(30), nullable=False)
    rank_projection_basis: Mapped[str | None] = mapped_column(String(80), nullable=True)
    selected_exam_ids_json: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    calculation_detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")


class RecommendationScheme(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "recommendation_scheme"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    student_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    results = relationship("RecommendationResult", back_populates="scheme", cascade="all, delete-orphan")


class VolunteerDraft(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "volunteer_draft"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    province: Mapped[str] = mapped_column(String(50), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    batch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exam_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    candidate_type: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    score_input_mode: Mapped[str] = mapped_column(String(50), default="actual_rank", nullable=False)
    score_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_range_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank_range_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_exam_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    use_historical_mapping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_preference: Mapped[str] = mapped_column(String(30), default="balanced", nullable=False)
    target_regions_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    school_level_tags_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    major_keyword: Mapped[str | None] = mapped_column(String(150), nullable=True)
    subject_combination: Mapped[str | None] = mapped_column(String(100), nullable=True)
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
    student_rank_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comprehensive_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    professional_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    culture_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    student = relationship("Student")
    exam = relationship("Exam")
    primary_direction = relationship("EmploymentDirection", foreign_keys=[primary_direction_id])
    secondary_direction = relationship("EmploymentDirection", foreign_keys=[secondary_direction_id])
    alternative_direction = relationship("EmploymentDirection", foreign_keys=[alternative_direction_id])
    items = relationship("VolunteerDraftItem", back_populates="draft", cascade="all, delete-orphan")


class VolunteerDraftItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "volunteer_draft_item"
    __table_args__ = (UniqueConstraint("draft_id", "sort_order", name="uq_volunteer_draft_item_order"),)

    draft_id: Mapped[int] = mapped_column(ForeignKey("volunteer_draft.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_id: Mapped[int | None] = mapped_column(ForeignKey("enrollment_plan.id"), nullable=True)
    candidate_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    draft = relationship("VolunteerDraft", back_populates="items")
    plan = relationship("EnrollmentPlan")


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
