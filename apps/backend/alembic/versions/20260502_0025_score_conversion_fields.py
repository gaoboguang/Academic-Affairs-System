"""Add score conversion fields

Revision ID: 20260502_0025
Revises: 20260502_0024
Create Date: 2026-05-02 11:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260502_0025"
down_revision: str | None = "20260502_0024"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "score_import_profile",
        sa.Column("subject_score_type_json", sa.JSON(), nullable=False, server_default="{}"),
    )

    op.add_column("score_record", sa.Column("original_score", sa.Float(), nullable=True))
    op.add_column("score_record", sa.Column("converted_score", sa.Float(), nullable=True))
    op.add_column(
        "score_record",
        sa.Column("score_value_type", sa.String(length=20), nullable=False, server_default="original"),
    )

    op.add_column(
        "score_total_snapshot",
        sa.Column("score_value_type", sa.String(length=20), nullable=False, server_default="original"),
    )

    op.add_column("score_subject_snapshot", sa.Column("original_score", sa.Float(), nullable=True))
    op.add_column("score_subject_snapshot", sa.Column("converted_score", sa.Float(), nullable=True))
    op.add_column(
        "score_subject_snapshot",
        sa.Column("score_value_type", sa.String(length=20), nullable=False, server_default="original"),
    )

    op.execute("UPDATE score_record SET original_score = score WHERE original_score IS NULL AND score IS NOT NULL")
    op.execute(
        "UPDATE score_subject_snapshot SET original_score = score "
        "WHERE original_score IS NULL AND score IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("score_subject_snapshot", "score_value_type")
    op.drop_column("score_subject_snapshot", "converted_score")
    op.drop_column("score_subject_snapshot", "original_score")
    op.drop_column("score_total_snapshot", "score_value_type")
    op.drop_column("score_record", "score_value_type")
    op.drop_column("score_record", "converted_score")
    op.drop_column("score_record", "original_score")
    op.drop_column("score_import_profile", "subject_score_type_json")
