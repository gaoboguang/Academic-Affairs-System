"""Add class honor schema

Revision ID: 20260502_0027
Revises: 20260502_0026
Create Date: 2026-05-02 18:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260502_0027"
down_revision: str | None = "20260502_0026"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "class_honor",
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("honor_level", sa.String(length=50), nullable=True),
        sa.Column("awarded_on", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=150), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["school_class.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "title", "awarded_on", name="uq_class_honor_class_title_date"),
    )
    op.create_index("ix_class_honor_class_id", "class_honor", ["class_id"])
    op.create_index("ix_class_honor_awarded_on", "class_honor", ["awarded_on"])


def downgrade() -> None:
    op.drop_index("ix_class_honor_awarded_on", table_name="class_honor")
    op.drop_index("ix_class_honor_class_id", table_name="class_honor")
    op.drop_table("class_honor")
