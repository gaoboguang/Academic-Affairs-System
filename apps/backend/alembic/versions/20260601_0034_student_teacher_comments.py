from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260601_0034"
down_revision = "20260601_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_teacher_comment",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("semester_id", sa.Integer(), nullable=True),
        sa.Column("commented_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["semester_id"], ["semester.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_student_teacher_comment_student_active_time",
        "student_teacher_comment",
        ["student_id", "is_active", "commented_at"],
        unique=False,
    )
    op.create_index(
        "ix_student_teacher_comment_teacher_time",
        "student_teacher_comment",
        ["teacher_id", "commented_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_student_teacher_comment_teacher_time", table_name="student_teacher_comment")
    op.drop_index("ix_student_teacher_comment_student_active_time", table_name="student_teacher_comment")
    op.drop_table("student_teacher_comment")
