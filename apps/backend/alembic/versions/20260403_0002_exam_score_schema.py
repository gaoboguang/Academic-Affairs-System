"""Exam and score schema

Revision ID: 20260403_0002
Revises: 20260403_0001
Create Date: 2026-04-03 21:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260403_0002"
down_revision: str | None = "20260403_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "exam",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("exam_type", sa.String(length=50), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("grade_scope_json", sa.JSON(), nullable=True),
        sa.Column("is_trend_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "exam_subject",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=False),
        sa.Column("full_score", sa.Float(), nullable=False),
        sa.Column("is_in_total", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("excellent_line", sa.Float(), nullable=True),
        sa.Column("pass_line", sa.Float(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),
    )
    op.create_table(
        "score_import_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("import_time", sa.DateTime(), nullable=False),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("success_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_report_path", sa.String(length=255), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "score_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("score_status", sa.String(length=30), nullable=False),
        sa.Column("raw_text", sa.String(length=100), nullable=True),
        sa.Column("import_batch_id", sa.Integer(), sa.ForeignKey("score_import_batch.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_record"),
    )
    op.create_table(
        "score_total_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("class_rank", sa.Integer(), nullable=True),
        sa.Column("grade_rank", sa.Integer(), nullable=True),
        sa.Column("class_percentile", sa.Float(), nullable=True),
        sa.Column("grade_percentile", sa.Float(), nullable=True),
        sa.Column("rank_mode", sa.String(length=30), nullable=False),
        sa.Column("rebuilt_at", sa.DateTime(), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_score_total_snapshot"),
    )
    op.create_table(
        "score_subject_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("class_rank", sa.Integer(), nullable=True),
        sa.Column("grade_rank", sa.Integer(), nullable=True),
        sa.Column("class_percentile", sa.Float(), nullable=True),
        sa.Column("grade_percentile", sa.Float(), nullable=True),
        sa.Column("excellent_flag", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("pass_flag", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("exam_id", "student_id", "subject_id", name="uq_score_subject_snapshot"),
    )


def downgrade() -> None:
    op.drop_table("score_subject_snapshot")
    op.drop_table("score_total_snapshot")
    op.drop_table("score_record")
    op.drop_table("score_import_batch")
    op.drop_table("exam_subject")
    op.drop_table("exam")

