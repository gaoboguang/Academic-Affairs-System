"""Add student class transfer audit schema

Revision ID: 20260426_0019
Revises: 20260425_0018
Create Date: 2026-04-26 15:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260426_0019"
down_revision: str | None = "20260425_0018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_class_transfer_batch",
        sa.Column("source_class_id", sa.Integer(), nullable=True),
        sa.Column("target_class_id", sa.Integer(), nullable=False),
        sa.Column("target_grade_id", sa.Integer(), nullable=True),
        sa.Column("effective_on", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("operator_name", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("requested_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("success_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("blocked_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("confirm_text", sa.String(length=80), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["source_class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["target_class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["target_grade_id"], ["grade.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_class_transfer_batch_target",
        "student_class_transfer_batch",
        ["target_class_id", "effective_on"],
    )

    op.create_table(
        "student_class_transfer_item",
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("requested_student_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=True),
        sa.Column("student_no_snapshot", sa.String(length=50), nullable=True),
        sa.Column("student_name_snapshot", sa.String(length=100), nullable=True),
        sa.Column("from_grade_id", sa.Integer(), nullable=True),
        sa.Column("from_grade_name_snapshot", sa.String(length=50), nullable=True),
        sa.Column("from_class_id", sa.Integer(), nullable=True),
        sa.Column("from_class_name_snapshot", sa.String(length=50), nullable=True),
        sa.Column("to_grade_id", sa.Integer(), nullable=True),
        sa.Column("to_grade_name_snapshot", sa.String(length=50), nullable=True),
        sa.Column("to_class_id", sa.Integer(), nullable=True),
        sa.Column("to_class_name_snapshot", sa.String(length=50), nullable=True),
        sa.Column("before_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("after_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["student_class_transfer_batch.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.ForeignKeyConstraint(["from_grade_id"], ["grade.id"]),
        sa.ForeignKeyConstraint(["from_class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["to_grade_id"], ["grade.id"]),
        sa.ForeignKeyConstraint(["to_class_id"], ["school_class.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_class_transfer_item_student",
        "student_class_transfer_item",
        ["student_id", "batch_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_class_transfer_item_student", table_name="student_class_transfer_item")
    op.drop_table("student_class_transfer_item")
    op.drop_index("ix_student_class_transfer_batch_target", table_name="student_class_transfer_batch")
    op.drop_table("student_class_transfer_batch")
