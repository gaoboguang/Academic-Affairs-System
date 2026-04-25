"""Add student gaokao score projection snapshots

Revision ID: 20260425_0017
Revises: 20260425_0016
Create Date: 2026-04-25 16:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260425_0017"
down_revision: str | None = "20260425_0016"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_gaokao_score_projection",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), server_default="山东", nullable=False),
        sa.Column("source_mode", sa.String(length=50), nullable=False),
        sa.Column("predicted_score", sa.Float(), nullable=True),
        sa.Column("predicted_rank", sa.Integer(), nullable=True),
        sa.Column("rank_range_low", sa.Integer(), nullable=True),
        sa.Column("rank_range_high", sa.Integer(), nullable=True),
        sa.Column("confidence_level", sa.String(length=30), nullable=False),
        sa.Column("rank_projection_basis", sa.String(length=80), nullable=True),
        sa.Column("selected_exam_ids_json", sa.JSON(), nullable=True),
        sa.Column("calculation_detail_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_gaokao_projection_student_year",
        "student_gaokao_score_projection",
        ["student_id", "target_year"],
    )
    op.create_index(
        "ix_student_gaokao_projection_source_mode",
        "student_gaokao_score_projection",
        ["source_mode"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_gaokao_projection_source_mode", table_name="student_gaokao_score_projection")
    op.drop_index("ix_student_gaokao_projection_student_year", table_name="student_gaokao_score_projection")
    op.drop_table("student_gaokao_score_projection")
