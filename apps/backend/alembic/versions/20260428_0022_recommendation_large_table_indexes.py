"""Add indexes for large recommendation tables

Revision ID: 20260428_0022
Revises: 20260428_0021
Create Date: 2026-04-28 16:00:00
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260428_0022"
down_revision: str | None = "20260428_0021"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_admission_record_list_filters",
        "admission_record",
        ["is_active", "province", "year", "student_type", "college_id", "batch"],
    )
    op.create_index(
        "ix_enrollment_plan_list_filters",
        "enrollment_plan",
        ["is_active", "province", "year", "student_type", "batch", "college_id"],
    )
    op.create_index(
        "ix_enrollment_plan_keyword_snapshot",
        "enrollment_plan",
        ["major_name_snapshot", "major_group_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_enrollment_plan_keyword_snapshot", table_name="enrollment_plan")
    op.drop_index("ix_enrollment_plan_list_filters", table_name="enrollment_plan")
    op.drop_index("ix_admission_record_list_filters", table_name="admission_record")
