"""Timetable and workload schema

Revision ID: 20260403_0003
Revises: 20260403_0002
Create Date: 2026-04-03 22:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260403_0003"
down_revision: str | None = "20260403_0002"
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
        "timetable_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("import_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "timetable_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("timetable_batch.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("period_no", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=True),
        sa.Column("course_type", sa.String(length=50), nullable=True),
        sa.Column("week_rule", sa.String(length=30), nullable=False),
        sa.Column("week_list_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("mapping_status", sa.String(length=30), nullable=False),
        sa.Column("raw_teacher_name", sa.String(length=100), nullable=True),
        sa.Column("raw_class_name", sa.String(length=100), nullable=True),
        sa.Column("raw_subject_name", sa.String(length=100), nullable=True),
        sa.Column("raw_course_type", sa.String(length=100), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "period_definition",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("period_no", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("period_type", sa.String(length=30), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("period_no", name="uq_period_definition_period_no"),
    )
    op.create_table(
        "workload_rule_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "workload_rule_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_version_id", sa.Integer(), sa.ForeignKey("workload_rule_version.id"), nullable=False),
        sa.Column("dimension_type", sa.String(length=30), nullable=False),
        sa.Column("match_key", sa.String(length=100), nullable=False),
        sa.Column("coefficient", sa.Float(), nullable=True),
        sa.Column("fixed_value", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "teacher_workload_extra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("item_name", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Float(), server_default="0", nullable=False),
        sa.Column("coefficient", sa.Float(), server_default="1", nullable=False),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "teacher_workload_result",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("rule_version_id", sa.Integer(), sa.ForeignKey("workload_rule_version.id"), nullable=False),
        sa.Column("weekly_hours", sa.Float(), server_default="0", nullable=False),
        sa.Column("monthly_hours_json", sa.JSON(), nullable=True),
        sa.Column("semester_hours", sa.Float(), server_default="0", nullable=False),
        sa.Column("semester_workload", sa.Float(), server_default="0", nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("teacher_id", "semester_id", "rule_version_id", name="uq_teacher_workload_result"),
    )


def downgrade() -> None:
    op.drop_table("teacher_workload_result")
    op.drop_table("teacher_workload_extra")
    op.drop_table("workload_rule_item")
    op.drop_table("workload_rule_version")
    op.drop_table("period_definition")
    op.drop_table("timetable_entry")
    op.drop_table("timetable_batch")

