from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class EvaluationTemplate(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "evaluation_template"

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    target_type: Mapped[str] = mapped_column(String(50), default="teacher", nullable=False)
    weight_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    questions = relationship(
        "EvaluationQuestion",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    batches = relationship("EvaluationBatch", back_populates="template")


class EvaluationQuestion(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "evaluation_question"

    template_id: Mapped[int] = mapped_column(ForeignKey("evaluation_template.id"), nullable=False)
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    question_text: Mapped[str] = mapped_column(String(255), nullable=False)
    score_max: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template = relationship("EvaluationTemplate", back_populates="questions")


class EvaluationBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "evaluation_batch"

    template_id: Mapped[int] = mapped_column(ForeignKey("evaluation_template.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_time: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)

    template = relationship("EvaluationTemplate", back_populates="batches")
    semester = relationship("Semester")
    responses = relationship("EvaluationResponse", back_populates="batch", cascade="all, delete-orphan")
    summaries = relationship("EvaluationSummary", back_populates="batch", cascade="all, delete-orphan")


class EvaluationResponse(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "evaluation_response"

    batch_id: Mapped[int] = mapped_column(ForeignKey("evaluation_batch.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("evaluation_question.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    respondent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    batch = relationship("EvaluationBatch", back_populates="responses")
    teacher = relationship("Teacher")
    school_class = relationship("SchoolClass")
    question = relationship("EvaluationQuestion")


class EvaluationSummary(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "evaluation_summary"

    batch_id: Mapped[int] = mapped_column(ForeignKey("evaluation_batch.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    dimension_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, nullable=False)
    response_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    batch = relationship("EvaluationBatch", back_populates="summaries")
    teacher = relationship("Teacher")


class AdviserQuantRuleVersion(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "adviser_quant_rule_version"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    semester_id: Mapped[int | None] = mapped_column(ForeignKey("semester.id"), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester = relationship("Semester")
    items = relationship("AdviserQuantRuleItem", back_populates="rule_version", cascade="all, delete-orphan")


class AdviserQuantRuleItem(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "adviser_quant_rule_item"

    rule_version_id: Mapped[int] = mapped_column(ForeignKey("adviser_quant_rule_version.id"), nullable=False)
    item_name: Mapped[str] = mapped_column(String(150), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    default_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    requires_attachment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rule_version = relationship("AdviserQuantRuleVersion", back_populates="items")


class AdviserQuantRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "adviser_quant_record"

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    rule_item_id: Mapped[int] = mapped_column(ForeignKey("adviser_quant_rule_item.id"), nullable=False)
    record_month: Mapped[str] = mapped_column(String(7), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.now, nullable=False)

    teacher = relationship("Teacher")
    school_class = relationship("SchoolClass")
    semester = relationship("Semester")
    rule_item = relationship("AdviserQuantRuleItem")
    attachments = relationship(
        "AdviserQuantRecordAttachment",
        back_populates="record",
        cascade="all, delete-orphan",
    )


class AdviserQuantRecordAttachment(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "adviser_quant_record_attachment"

    record_id: Mapped[int] = mapped_column(ForeignKey("adviser_quant_record.id"), nullable=False)
    stored_file_id: Mapped[int] = mapped_column(ForeignKey("stored_file.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    record = relationship("AdviserQuantRecord", back_populates="attachments")
    stored_file = relationship("StoredFile")
