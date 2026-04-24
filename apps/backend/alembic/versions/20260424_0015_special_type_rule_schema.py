"""Add special type rule dictionary table

Revision ID: 20260424_0015
Revises: 20260422_0014
Create Date: 2026-04-24 15:40:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260424_0015"
down_revision: str | None = "20260422_0014"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "special_type_rule",
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("student_type", sa.String(length=50), nullable=False),
        sa.Column("category_code", sa.String(length=100), nullable=False),
        sa.Column("category_label", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("match_keywords_json", sa.JSON(), nullable=True),
        sa.Column("review_notes_json", sa.JSON(), nullable=True),
        sa.Column("priority_bonus", sa.Integer(), server_default="0", nullable=False),
        sa.Column("priority_notes_json", sa.JSON(), nullable=True),
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
            "student_type",
            "category_code",
            name="uq_special_type_rule_core",
        ),
    )


def downgrade() -> None:
    op.drop_table("special_type_rule")
