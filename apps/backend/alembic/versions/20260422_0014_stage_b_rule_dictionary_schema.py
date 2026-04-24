"""Add score transform and subject requirement dictionary tables

Revision ID: 20260422_0014
Revises: 20260410_0013
Create Date: 2026-04-22 15:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260422_0014"
down_revision: str | None = "20260410_0013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "province_score_transform_rule",
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("exam_mode", sa.String(length=50), server_default="", nullable=False),
        sa.Column("subject_code", sa.String(length=50), nullable=True),
        sa.Column("subject_name", sa.String(length=50), nullable=False),
        sa.Column("score_mode", sa.String(length=30), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("grade_table_json", sa.JSON(), nullable=True),
        sa.Column("formula_json", sa.JSON(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "subject_name",
            name="uq_province_score_transform_rule_core",
        ),
    )
    op.create_table(
        "subject_requirement_dict",
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("exam_mode", sa.String(length=50), server_default="", nullable=False),
        sa.Column("requirement_code", sa.String(length=100), nullable=False),
        sa.Column("requirement_text", sa.String(length=150), nullable=False),
        sa.Column("match_mode", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("normalized_subjects_json", sa.JSON(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "province",
            "year",
            "exam_mode",
            "requirement_code",
            name="uq_subject_requirement_dict_core",
        ),
    )


def downgrade() -> None:
    op.drop_table("subject_requirement_dict")
    op.drop_table("province_score_transform_rule")
