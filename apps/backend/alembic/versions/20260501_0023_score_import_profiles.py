"""Add score import profiles

Revision ID: 20260501_0023
Revises: 20260428_0022
Create Date: 2026-05-01 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260501_0023"
down_revision: str | None = "20260428_0022"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "score_import_profile",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("layout_type", sa.String(length=20), nullable=False),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.Column("header_row", sa.Integer(), nullable=False),
        sa.Column("field_mapping_json", sa.JSON(), nullable=False),
        sa.Column("subject_mapping_json", sa.JSON(), nullable=False),
        sa.Column("ignored_columns_json", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_score_import_profile_name"),
    )
    with op.batch_alter_table("score_import_batch", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("profile_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("detection_summary_json", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_score_import_batch_profile_id",
            "score_import_profile",
            ["profile_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("score_import_batch", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_score_import_batch_profile_id", type_="foreignkey")
        batch_op.drop_column("detection_summary_json")
        batch_op.drop_column("profile_id")
    op.drop_table("score_import_profile")
