"""Add student origin province field

Revision ID: 20260410_0013
Revises: 20260410_0012
Create Date: 2026-04-10 21:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0013"
down_revision: str | None = "20260410_0012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("student") as batch_op:
        batch_op.add_column(sa.Column("origin_province", sa.String(length=50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("student") as batch_op:
        batch_op.drop_column("origin_province")
