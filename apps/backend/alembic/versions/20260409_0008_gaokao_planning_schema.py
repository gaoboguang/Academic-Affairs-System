"""Gaokao planning schema

Revision ID: 20260409_0008
Revises: 20260404_0007
Create Date: 2026-04-09 21:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0008"
down_revision: str | None = "20260404_0007"
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
        "enrollment_plan",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("batch", sa.String(length=50), nullable=False),
        sa.Column("exam_mode", sa.String(length=50), nullable=False),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("college.id"), nullable=False),
        sa.Column("major_id", sa.Integer(), sa.ForeignKey("major.id"), nullable=True),
        sa.Column("college_code_snapshot", sa.String(length=50), nullable=True),
        sa.Column("major_group_code", sa.String(length=50), server_default="", nullable=False),
        sa.Column("major_name_snapshot", sa.String(length=150), server_default="", nullable=False),
        sa.Column("major_code_snapshot", sa.String(length=50), nullable=True),
        sa.Column("plan_count", sa.Integer(), nullable=False),
        sa.Column("subject_requirement", sa.String(length=150), nullable=True),
        sa.Column("tuition_fee", sa.String(length=100), nullable=True),
        sa.Column("schooling_years", sa.String(length=50), nullable=True),
        sa.Column("training_location", sa.String(length=100), nullable=True),
        sa.Column("student_type", sa.String(length=50), server_default="general", nullable=False),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("import_batch_name", sa.String(length=100), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint(
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
    op.create_table(
        "province_volunteer_rule",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("exam_mode", sa.String(length=50), nullable=False),
        sa.Column("batch", sa.String(length=50), nullable=False),
        sa.Column("batch_order", sa.Integer(), nullable=True),
        sa.Column("volunteer_limit", sa.Integer(), nullable=False),
        sa.Column("volunteer_unit_type", sa.String(length=50), nullable=False),
        sa.Column("is_parallel", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("allow_adjustment", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("special_rules_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "batch",
            name="uq_province_volunteer_rule_core",
        ),
    )


def downgrade() -> None:
    op.drop_table("province_volunteer_rule")
    op.drop_table("enrollment_plan")
