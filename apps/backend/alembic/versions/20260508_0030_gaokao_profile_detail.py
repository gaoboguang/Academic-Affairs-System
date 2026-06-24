"""Add gaokao college and major profile details

Revision ID: 20260508_0030
Revises: 20260502_0029
Create Date: 2026-05-08 09:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0030"
down_revision: str | None = "20260502_0029"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "college_profile_detail",
        sa.Column("college_id", sa.Integer(), nullable=False),
        sa.Column("enrollment_code", sa.String(length=50), nullable=True),
        sa.Column("authority_department", sa.String(length=150), nullable=True),
        sa.Column("education_level", sa.String(length=80), nullable=True),
        sa.Column("is_985", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_211", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_dual_class", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("ruanke_rank", sa.Integer(), nullable=True),
        sa.Column("eol_rank", sa.Integer(), nullable=True),
        sa.Column("area", sa.String(length=100), nullable=True),
        sa.Column("master_program_count", sa.Integer(), nullable=True),
        sa.Column("doctor_program_count", sa.Integer(), nullable=True),
        sa.Column("official_website", sa.String(length=255), nullable=True),
        sa.Column("admission_website", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["college_id"], ["college.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("college_id", name="uq_college_profile_detail_college"),
    )
    op.create_index("ix_college_profile_detail_enrollment_code", "college_profile_detail", ["enrollment_code"])
    op.create_index("ix_college_profile_detail_source_sha256", "college_profile_detail", ["source_sha256"])

    op.create_table(
        "college_year_summary",
        sa.Column("college_id", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("total_plan_count", sa.Integer(), nullable=True),
        sa.Column("specialty_count", sa.Integer(), nullable=True),
        sa.Column("min_rank", sa.Integer(), nullable=True),
        sa.Column("estimated_min_score", sa.Float(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["college_id"], ["college.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("college_id", "province", "year", name="uq_college_year_summary_core"),
    )
    op.create_index("ix_college_year_summary_college_year", "college_year_summary", ["college_id", "year"])
    op.create_index("ix_college_year_summary_province_year", "college_year_summary", ["province", "year"])

    op.create_table(
        "major_profile_detail",
        sa.Column("major_id", sa.Integer(), nullable=False),
        sa.Column("major_code", sa.String(length=50), nullable=True),
        sa.Column("education_level", sa.String(length=80), nullable=True),
        sa.Column("schooling_years", sa.String(length=50), nullable=True),
        sa.Column("direction", sa.String(length=150), nullable=True),
        sa.Column("tags_json", sa.JSON(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["major_id"], ["major.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("major_id", name="uq_major_profile_detail_major"),
    )
    op.create_index("ix_major_profile_detail_major_code", "major_profile_detail", ["major_code"])
    op.create_index("ix_major_profile_detail_source_sha256", "major_profile_detail", ["source_sha256"])

    op.create_table(
        "college_major_profile",
        sa.Column("college_id", sa.Integer(), nullable=False),
        sa.Column("major_id", sa.Integer(), nullable=False),
        sa.Column("school_major_feature", sa.Text(), nullable=True),
        sa.Column("is_national_feature", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_provincial_feature", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("is_key_major", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("schooling_years", sa.String(length=50), nullable=True),
        sa.Column("education_level", sa.String(length=80), nullable=True),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["college_id"], ["college.id"]),
        sa.ForeignKeyConstraint(["major_id"], ["major.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("college_id", "major_id", name="uq_college_major_profile_core"),
    )
    op.create_index("ix_college_major_profile_college", "college_major_profile", ["college_id"])
    op.create_index("ix_college_major_profile_major", "college_major_profile", ["major_id"])
    op.create_index("ix_college_major_profile_source_sha256", "college_major_profile", ["source_sha256"])


def downgrade() -> None:
    op.drop_index("ix_college_major_profile_source_sha256", table_name="college_major_profile")
    op.drop_index("ix_college_major_profile_major", table_name="college_major_profile")
    op.drop_index("ix_college_major_profile_college", table_name="college_major_profile")
    op.drop_table("college_major_profile")

    op.drop_index("ix_major_profile_detail_source_sha256", table_name="major_profile_detail")
    op.drop_index("ix_major_profile_detail_major_code", table_name="major_profile_detail")
    op.drop_table("major_profile_detail")

    op.drop_index("ix_college_year_summary_province_year", table_name="college_year_summary")
    op.drop_index("ix_college_year_summary_college_year", table_name="college_year_summary")
    op.drop_table("college_year_summary")

    op.drop_index("ix_college_profile_detail_source_sha256", table_name="college_profile_detail")
    op.drop_index("ix_college_profile_detail_enrollment_code", table_name="college_profile_detail")
    op.drop_table("college_profile_detail")
