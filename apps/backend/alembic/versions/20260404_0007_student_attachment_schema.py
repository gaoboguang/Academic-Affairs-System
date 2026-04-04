"""Student attachment schema

Revision ID: 20260404_0007
Revises: 20260404_0006
Create Date: 2026-04-04 17:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0007"
down_revision: str | None = "20260404_0006"
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
        "student_attachment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("stored_file_id", sa.Integer(), sa.ForeignKey("stored_file.id"), nullable=False),
        sa.Column("attachment_type", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.UniqueConstraint("student_id", "stored_file_id", name="uq_student_attachment_file"),
        *_timestamp_columns(),
    )


def downgrade() -> None:
    op.drop_table("student_attachment")
