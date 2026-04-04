"""Evaluation and adviser quant schema

Revision ID: 20260404_0006
Revises: 20260404_0005
Create Date: 2026-04-04 14:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0006"
down_revision: str | None = "20260404_0005"
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
        "evaluation_template",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("weight_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "evaluation_question",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("evaluation_template.id"), nullable=False),
        sa.Column("dimension_name", sa.String(length=100), nullable=False),
        sa.Column("question_text", sa.String(length=255), nullable=False),
        sa.Column("score_max", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamp_columns(),
    )
    op.create_table(
        "evaluation_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("evaluation_template.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("import_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "evaluation_response",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("evaluation_batch.id"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("evaluation_question.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("respondent_type", sa.String(length=50), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "evaluation_summary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("evaluation_batch.id"), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("dimension_name", sa.String(length=100), nullable=False),
        sa.Column("avg_score", sa.Float(), nullable=False),
        sa.Column("response_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "adviser_quant_rule_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "adviser_quant_rule_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_version_id", sa.Integer(), sa.ForeignKey("adviser_quant_rule_version.id"), nullable=False),
        sa.Column("item_name", sa.String(length=150), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("default_score", sa.Float(), nullable=False),
        sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamp_columns(),
    )
    op.create_table(
        "adviser_quant_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("rule_item_id", sa.Integer(), sa.ForeignKey("adviser_quant_rule_item.id"), nullable=False),
        sa.Column("record_month", sa.String(length=7), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "adviser_quant_record_attachment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("record_id", sa.Integer(), sa.ForeignKey("adviser_quant_record.id"), nullable=False),
        sa.Column("stored_file_id", sa.Integer(), sa.ForeignKey("stored_file.id"), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        *_timestamp_columns(),
    )


def downgrade() -> None:
    op.drop_table("adviser_quant_record_attachment")
    op.drop_table("adviser_quant_record")
    op.drop_table("adviser_quant_rule_item")
    op.drop_table("adviser_quant_rule_version")
    op.drop_table("evaluation_summary")
    op.drop_table("evaluation_response")
    op.drop_table("evaluation_batch")
    op.drop_table("evaluation_question")
    op.drop_table("evaluation_template")
