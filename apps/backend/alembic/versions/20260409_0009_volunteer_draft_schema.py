"""Volunteer draft schema

Revision ID: 20260409_0009
Revises: 20260409_0008
Create Date: 2026-04-09 22:50:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0009"
down_revision: str | None = "20260409_0008"
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
        "volunteer_draft",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("batch", sa.String(length=50), nullable=True),
        sa.Column("exam_mode", sa.String(length=50), nullable=True),
        sa.Column("target_regions_json", sa.JSON(), nullable=True),
        sa.Column("school_level_tags_json", sa.JSON(), nullable=True),
        sa.Column("major_keyword", sa.String(length=150), nullable=True),
        sa.Column("subject_combination", sa.String(length=100), nullable=True),
        sa.Column("student_rank_override", sa.Integer(), nullable=True),
        sa.Column("comprehensive_score", sa.Float(), nullable=True),
        sa.Column("professional_score", sa.Float(), nullable=True),
        sa.Column("culture_score", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("rule_snapshot_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "volunteer_draft_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_id", sa.Integer(), sa.ForeignKey("volunteer_draft.id"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("enrollment_plan.id"), nullable=True),
        sa.Column("candidate_snapshot_json", sa.JSON(), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("draft_id", "sort_order", name="uq_volunteer_draft_item_order"),
    )


def downgrade() -> None:
    op.drop_table("volunteer_draft_item")
    op.drop_table("volunteer_draft")
