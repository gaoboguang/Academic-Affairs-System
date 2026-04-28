"""Add student planning goal and task schema

Revision ID: 20260428_0021
Revises: 20260427_0020
Create Date: 2026-04-28 09:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260428_0021"
down_revision: str | None = "20260427_0020"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "student_planning_goal",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("pathway_code", sa.String(length=80), nullable=False),
        sa.Column("pathway_name", sa.String(length=120), nullable=False),
        sa.Column("target_college", sa.String(length=150), nullable=True),
        sa.Column("target_major", sa.String(length=150), nullable=True),
        sa.Column("target_score", sa.Float(), nullable=True),
        sa.Column("target_rank", sa.Integer(), nullable=True),
        sa.Column("backup_pathways", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="in_progress", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "target_year",
            "pathway_code",
            "is_active",
            name="uq_student_planning_goal_active_pathway",
        ),
    )
    op.create_index(
        "ix_student_planning_goal_student_year",
        "student_planning_goal",
        ["student_id", "target_year", "status"],
    )

    op.create_table(
        "student_planning_task",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=50), server_default="manual", nullable=False),
        sa.Column("source_ref_id", sa.String(length=120), nullable=True),
        sa.Column("task_type", sa.String(length=50), server_default="other", nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="not_started", nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("related_route", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["student_planning_goal.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "source_type",
            "source_ref_id",
            "task_type",
            "title",
            "is_active",
            name="uq_student_planning_task_source",
        ),
    )
    op.create_index(
        "ix_student_planning_task_student_status_due",
        "student_planning_task",
        ["student_id", "status", "due_date"],
    )

    op.create_table(
        "student_planning_note",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("goal_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("note_type", sa.String(length=50), server_default="review", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["student_planning_goal.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["student_planning_task.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_planning_note_student",
        "student_planning_note",
        ["student_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_planning_note_student", table_name="student_planning_note")
    op.drop_table("student_planning_note")
    op.drop_index("ix_student_planning_task_student_status_due", table_name="student_planning_task")
    op.drop_table("student_planning_task")
    op.drop_index("ix_student_planning_goal_student_year", table_name="student_planning_goal")
    op.drop_table("student_planning_goal")
