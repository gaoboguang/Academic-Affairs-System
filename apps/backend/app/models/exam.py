from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class Exam(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "exam"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semester.id"), nullable=False)
    grade_scope_json: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    is_trend_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    semester = relationship("Semester")
    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")
    score_records = relationship("ScoreRecord", back_populates="exam", cascade="all, delete-orphan")


class ExamSubject(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "exam_subject"
    __table_args__ = (UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    full_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_in_total: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    excellent_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_line: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exam = relationship("Exam", back_populates="subjects")
    subject = relationship("Subject")


class ScoreImportBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_import_batch"

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("score_import_profile.id"), nullable=True)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processing", nullable=False)
    error_report_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detection_summary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    exam = relationship("Exam")
    profile = relationship("ScoreImportProfile")
    records = relationship("ScoreRecord", back_populates="import_batch")


class ScoreQuestionImportBatch(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_question_import_batch"

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    import_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processing", nullable=False)
    error_report_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam")


class ScoreImportProfile(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_import_profile"
    __table_args__ = (UniqueConstraint("name", name="uq_score_import_profile_name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    layout_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sheet_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    header_row: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    field_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    subject_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    subject_score_type_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ignored_columns_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    metadata_mapping_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class ScoreRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_record"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_record"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    converted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_value_type: Mapped[str] = mapped_column(String(20), default="original", nullable=False)
    score_status: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    raw_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("score_import_batch.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam", back_populates="score_records")
    student = relationship("Student")
    subject = relationship("Subject")
    import_batch = relationship("ScoreImportBatch", back_populates="records")


class ScoreClassMapping(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_class_mapping"
    __table_args__ = (UniqueConstraint("exam_id", "source_class_name", name="uq_score_class_mapping"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    source_class_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mapped_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(30), default="mapped", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam")
    mapped_class = relationship("SchoolClass")


class ScoreExamStudentContext(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_exam_student_context"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_score_exam_student_context"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    source_class_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mapped_class_id: Mapped[int | None] = mapped_column(ForeignKey("school_class.id"), nullable=True)
    source_student_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_exam_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_total_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_school_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_grade_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_row_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(30), default="mapped", nullable=False)
    raw_meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam")
    student = relationship("Student")
    mapped_class = relationship("SchoolClass")


class ScoreTargetLine(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_target_line"
    __table_args__ = (UniqueConstraint("exam_id", "name", name="uq_score_target_line_exam_name"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    line_type: Mapped[str] = mapped_column(String(20), nullable=False)
    score_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    near_margin_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    near_margin_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam")


class KnowledgePoint(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "knowledge_point"
    __table_args__ = (UniqueConstraint("subject_id", "name", name="uq_knowledge_point_subject_name"),)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("knowledge_point.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)

    subject = relationship("Subject")
    parent = relationship("KnowledgePoint", remote_side="KnowledgePoint.id")


class KnowledgePointAlias(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "knowledge_point_alias"
    __table_args__ = (UniqueConstraint("subject_id", "alias_name", name="uq_knowledge_point_alias_subject_name"),)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("knowledge_point.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(String(120), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), default="manual", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject = relationship("Subject")
    knowledge_point = relationship("KnowledgePoint")


class ErrorReasonTag(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "error_reason_tag"
    __table_args__ = (UniqueConstraint("name", name="uq_error_reason_tag_name"),)

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ScoreQuestion(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_question"
    __table_args__ = (UniqueConstraint("exam_id", "subject_id", "question_no", name="uq_score_question"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    question_no: Mapped[str] = mapped_column(String(50), nullable=False)
    full_score: Mapped[float] = mapped_column(Float, nullable=False)
    question_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ability_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exam = relationship("Exam")
    subject = relationship("Subject")


class ScoreQuestionKnowledgePoint(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_question_knowledge_point"
    __table_args__ = (
        UniqueConstraint("question_id", "knowledge_point_id", name="uq_score_question_knowledge_point"),
    )

    question_id: Mapped[int] = mapped_column(ForeignKey("score_question.id"), nullable=False)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("knowledge_point.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    match_source: Mapped[str] = mapped_column(String(30), default="standard", nullable=False)
    raw_knowledge_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    question = relationship("ScoreQuestion")
    knowledge_point = relationship("KnowledgePoint")


class ScoreQuestionRecord(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_question_record"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", "question_id", name="uq_score_question_record"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("score_question.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_status: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    raw_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_tags_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    error_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("score_question_import_batch.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam")
    student = relationship("Student")
    subject = relationship("Subject")
    question = relationship("ScoreQuestion")
    import_batch = relationship("ScoreQuestionImportBatch")


class ScoreKnowledgeSnapshot(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_knowledge_snapshot"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "subject_id", "knowledge_point_id", name="uq_score_knowledge_snapshot"),
    )

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    knowledge_point_id: Mapped[int] = mapped_column(ForeignKey("knowledge_point.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    full_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    score_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_average_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_gap_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    lost_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    question_numbers_json: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    diagnosis_label: Mapped[str] = mapped_column(String(50), default="正常", nullable=False)
    error_tags_json: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    dominant_error_tag: Mapped[str | None] = mapped_column(String(80), nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    rebuilt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )

    exam = relationship("Exam")
    student = relationship("Student")
    subject = relationship("Subject")
    knowledge_point = relationship("KnowledgePoint")


class ScoreTotalSnapshot(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_total_snapshot"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_score_total_snapshot"),)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_value_type: Mapped[str] = mapped_column(String(20), default="original", nullable=False)
    class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_mode: Mapped[str] = mapped_column(String(30), default="competition", nullable=False)
    rebuilt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.now, nullable=False
    )

    exam = relationship("Exam")
    student = relationship("Student")


class ScoreSubjectSnapshot(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "score_subject_snapshot"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_subject_snapshot"),
    )

    exam_id: Mapped[int] = mapped_column(ForeignKey("exam.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    converted_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_value_type: Mapped[str] = mapped_column(String(20), default="original", nullable=False)
    class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    excellent_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pass_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    exam = relationship("Exam")
    student = relationship("Student")
    subject = relationship("Subject")
