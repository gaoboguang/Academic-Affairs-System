"""Student career preference schema

Revision ID: 20260410_0011
Revises: 20260409_0010
Create Date: 2026-04-10 10:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260410_0011"
down_revision: str | None = "20260409_0010"
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
        "student_career_preference",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("primary_direction_id", sa.Integer(), sa.ForeignKey("employment_direction.id"), nullable=True),
        sa.Column("secondary_direction_id", sa.Integer(), sa.ForeignKey("employment_direction.id"), nullable=True),
        sa.Column("alternative_direction_id", sa.Integer(), sa.ForeignKey("employment_direction.id"), nullable=True),
        sa.Column("priority_focuses_json", sa.JSON(), nullable=True),
        sa.Column("preferred_industries_json", sa.JSON(), nullable=True),
        sa.Column("preferred_job_types_json", sa.JSON(), nullable=True),
        sa.Column("target_employment_cities_json", sa.JSON(), nullable=True),
        sa.Column("accepts_postgraduate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("accepts_public_service", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("accepts_certificate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("accepts_long_training", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("student_id", name="uq_student_career_preference_student"),
    )

    with op.batch_alter_table("volunteer_draft") as batch_op:
        batch_op.add_column(sa.Column("primary_direction_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("secondary_direction_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("alternative_direction_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("priority_focuses_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("preferred_industries_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("preferred_job_types_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("target_employment_cities_json", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("accepts_postgraduate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
        batch_op.add_column(
            sa.Column("accepts_public_service", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
        batch_op.add_column(
            sa.Column("accepts_certificate", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
        batch_op.add_column(
            sa.Column("accepts_long_training", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        )
        batch_op.create_foreign_key(
            "fk_volunteer_draft_primary_direction_id",
            "employment_direction",
            ["primary_direction_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_volunteer_draft_secondary_direction_id",
            "employment_direction",
            ["secondary_direction_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_volunteer_draft_alternative_direction_id",
            "employment_direction",
            ["alternative_direction_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("volunteer_draft") as batch_op:
        batch_op.drop_constraint("fk_volunteer_draft_alternative_direction_id", type_="foreignkey")
        batch_op.drop_constraint("fk_volunteer_draft_secondary_direction_id", type_="foreignkey")
        batch_op.drop_constraint("fk_volunteer_draft_primary_direction_id", type_="foreignkey")
        batch_op.drop_column("accepts_long_training")
        batch_op.drop_column("accepts_certificate")
        batch_op.drop_column("accepts_public_service")
        batch_op.drop_column("accepts_postgraduate")
        batch_op.drop_column("target_employment_cities_json")
        batch_op.drop_column("preferred_job_types_json")
        batch_op.drop_column("preferred_industries_json")
        batch_op.drop_column("priority_focuses_json")
        batch_op.drop_column("alternative_direction_id")
        batch_op.drop_column("secondary_direction_id")
        batch_op.drop_column("primary_direction_id")

    op.drop_table("student_career_preference")
