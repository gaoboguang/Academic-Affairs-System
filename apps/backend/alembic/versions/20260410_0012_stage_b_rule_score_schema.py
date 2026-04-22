"""Stage B province rule and score input schema

Revision ID: 20260410_0012
Revises: 20260410_0011
Create Date: 2026-04-10 19:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0012"
down_revision: str | None = "20260410_0011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("province_volunteer_rule", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("candidate_type", sa.String(length=50), server_default="", nullable=False))
        batch_op.add_column(sa.Column("total_score", sa.Integer(), server_default="750", nullable=False))
        batch_op.add_column(sa.Column("subject_requirement_mode", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("required_subjects_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("first_choice_subjects_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("reselect_subjects_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("score_rule_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("parallel_rule_mode", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("max_major_per_unit", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("support_collect_round", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch_op.drop_constraint("uq_province_volunteer_rule_core", type_="unique")
        batch_op.create_unique_constraint(
            "uq_province_volunteer_rule_core",
            ["province", "year", "exam_mode", "batch", "candidate_type"],
        )

    with op.batch_alter_table("volunteer_draft") as batch_op:
        batch_op.add_column(sa.Column("candidate_type", sa.String(length=50), server_default="", nullable=False))
        batch_op.add_column(sa.Column("score_input_mode", sa.String(length=50), server_default="actual_rank", nullable=False))
        batch_op.add_column(sa.Column("score_range_min", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("score_range_max", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("rank_range_min", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("rank_range_max", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reference_exam_name", sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column("use_historical_mapping", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch_op.add_column(sa.Column("risk_preference", sa.String(length=30), server_default="balanced", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("volunteer_draft") as batch_op:
        batch_op.drop_column("risk_preference")
        batch_op.drop_column("use_historical_mapping")
        batch_op.drop_column("reference_exam_name")
        batch_op.drop_column("rank_range_max")
        batch_op.drop_column("rank_range_min")
        batch_op.drop_column("score_range_max")
        batch_op.drop_column("score_range_min")
        batch_op.drop_column("score_input_mode")
        batch_op.drop_column("candidate_type")

    with op.batch_alter_table("province_volunteer_rule", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_province_volunteer_rule_core", type_="unique")
        batch_op.create_unique_constraint(
            "uq_province_volunteer_rule_core",
            ["province", "year", "exam_mode", "batch"],
        )
        batch_op.drop_column("support_collect_round")
        batch_op.drop_column("max_major_per_unit")
        batch_op.drop_column("parallel_rule_mode")
        batch_op.drop_column("score_rule_summary")
        batch_op.drop_column("reselect_subjects_json")
        batch_op.drop_column("first_choice_subjects_json")
        batch_op.drop_column("required_subjects_json")
        batch_op.drop_column("subject_requirement_mode")
        batch_op.drop_column("total_score")
        batch_op.drop_column("candidate_type")
