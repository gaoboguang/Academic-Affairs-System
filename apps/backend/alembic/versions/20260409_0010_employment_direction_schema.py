"""Employment direction schema

Revision ID: 20260409_0010
Revises: 20260409_0009
Create Date: 2026-04-09 23:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260409_0010"
down_revision: str | None = "20260409_0009"
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
        "employment_direction",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("alias_names_json", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("common_job_types_json", sa.JSON(), nullable=True),
        sa.Column("common_industries_json", sa.JSON(), nullable=True),
        sa.Column("prefers_postgraduate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("requires_certificate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("requires_long_cycle", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("supports_art", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("risk_note", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "major_employment_mapping",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("major_id", sa.Integer(), sa.ForeignKey("major.id"), nullable=False),
        sa.Column("direction_id", sa.Integer(), sa.ForeignKey("employment_direction.id"), nullable=False),
        sa.Column("strength", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("recommendation_note", sa.Text(), nullable=True),
        sa.Column("requires_postgraduate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("requires_certificate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("supported_student_types_json", sa.JSON(), nullable=True),
        sa.Column("supports_art", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("major_id", "direction_id", name="uq_major_employment_mapping_core"),
    )


def downgrade() -> None:
    op.drop_table("major_employment_mapping")
    op.drop_table("employment_direction")
