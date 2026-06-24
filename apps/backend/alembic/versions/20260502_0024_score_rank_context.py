"""Add score rank context and target lines

Revision ID: 20260502_0024
Revises: 20260501_0023
Create Date: 2026-05-02 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260502_0024"
down_revision: str | None = "20260501_0023"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "score_import_profile",
        sa.Column("metadata_mapping_json", sa.JSON(), nullable=False, server_default="{}"),
    )

    op.create_table(
        "score_class_mapping",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("source_class_name", sa.String(length=100), nullable=False),
        sa.Column("mapped_class_id", sa.Integer(), nullable=True),
        sa.Column("mapping_status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.ForeignKeyConstraint(["mapped_class_id"], ["school_class.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "source_class_name", name="uq_score_class_mapping"),
    )
    op.create_index("ix_score_class_mapping_exam_id", "score_class_mapping", ["exam_id"])

    op.create_table(
        "score_exam_student_context",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("source_class_name", sa.String(length=100), nullable=True),
        sa.Column("mapped_class_id", sa.Integer(), nullable=True),
        sa.Column("source_student_no", sa.String(length=100), nullable=True),
        sa.Column("source_exam_no", sa.String(length=100), nullable=True),
        sa.Column("source_total_score", sa.Float(), nullable=True),
        sa.Column("source_class_rank", sa.Integer(), nullable=True),
        sa.Column("source_school_rank", sa.Integer(), nullable=True),
        sa.Column("source_grade_rank", sa.Integer(), nullable=True),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("mapping_status", sa.String(length=30), nullable=False),
        sa.Column("raw_meta_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.ForeignKeyConstraint(["mapped_class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_score_exam_student_context"),
    )
    op.create_index("ix_score_exam_student_context_exam_id", "score_exam_student_context", ["exam_id"])
    op.create_index(
        "ix_score_exam_student_context_exam_class",
        "score_exam_student_context",
        ["exam_id", "mapped_class_id"],
    )

    op.create_table(
        "score_target_line",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("line_type", sa.String(length=20), nullable=False),
        sa.Column("score_value", sa.Float(), nullable=True),
        sa.Column("rank_value", sa.Integer(), nullable=True),
        sa.Column("near_margin_score", sa.Float(), nullable=True),
        sa.Column("near_margin_rank", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "name", name="uq_score_target_line_exam_name"),
    )
    op.create_index("ix_score_target_line_exam_id", "score_target_line", ["exam_id"])


def downgrade() -> None:
    op.drop_index("ix_score_target_line_exam_id", table_name="score_target_line")
    op.drop_table("score_target_line")
    op.drop_index("ix_score_exam_student_context_exam_class", table_name="score_exam_student_context")
    op.drop_index("ix_score_exam_student_context_exam_id", table_name="score_exam_student_context")
    op.drop_table("score_exam_student_context")
    op.drop_index("ix_score_class_mapping_exam_id", table_name="score_class_mapping")
    op.drop_table("score_class_mapping")
    op.drop_column("score_import_profile", "metadata_mapping_json")
