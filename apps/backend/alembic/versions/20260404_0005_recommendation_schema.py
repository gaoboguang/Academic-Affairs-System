"""College, admission, and recommendation schema

Revision ID: 20260404_0005
Revises: 20260404_0004
Create Date: 2026-04-04 12:55:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0005"
down_revision: str | None = "20260404_0004"
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
        "college",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("college_code", sa.String(length=50), nullable=True),
        sa.Column("province", sa.String(length=50), nullable=True),
        sa.Column("city", sa.String(length=50), nullable=True),
        sa.Column("school_type", sa.String(length=50), nullable=True),
        sa.Column("school_level_tags_json", sa.JSON(), nullable=True),
        sa.Column("intro", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("supports_art", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "college_alias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("college.id"), nullable=False),
        sa.Column("alias_name", sa.String(length=150), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("college_id", "alias_name", name="uq_college_alias_name"),
    )
    op.create_table(
        "major",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False, unique=True),
        sa.Column("major_code", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("direction", sa.String(length=150), nullable=True),
        sa.Column("career_path", sa.String(length=255), nullable=True),
        sa.Column("is_art_related", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "college_major",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("college.id"), nullable=False),
        sa.Column("major_id", sa.Integer(), sa.ForeignKey("major.id"), nullable=False),
        sa.Column("enrollment_note", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("college_id", "major_id", name="uq_college_major"),
    )
    op.create_table(
        "admission_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("batch", sa.String(length=50), nullable=False),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("college.id"), nullable=False),
        sa.Column("major_id", sa.Integer(), sa.ForeignKey("major.id"), nullable=True),
        sa.Column("student_type", sa.String(length=50), nullable=False),
        sa.Column("art_track", sa.String(length=50), nullable=True),
        sa.Column("subject_requirement", sa.String(length=100), nullable=True),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("min_rank", sa.Integer(), nullable=True),
        sa.Column("avg_score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("plan_count", sa.Integer(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "year",
            "province",
            "batch",
            "college_id",
            "major_id",
            "student_type",
            "art_track",
            name="uq_admission_record_core",
        ),
    )
    op.create_table(
        "recommendation_scheme",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("student_type", sa.String(length=50), nullable=False),
        sa.Column("rule_json", sa.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "recommendation_result",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("exam_id", sa.Integer(), sa.ForeignKey("exam.id"), nullable=False),
        sa.Column("scheme_id", sa.Integer(), sa.ForeignKey("recommendation_scheme.id"), nullable=False),
        sa.Column("result_type", sa.String(length=20), nullable=False),
        sa.Column("college_id", sa.Integer(), sa.ForeignKey("college.id"), nullable=False),
        sa.Column("major_id", sa.Integer(), sa.ForeignKey("major.id"), nullable=True),
        sa.Column("reference_rank", sa.Integer(), nullable=True),
        sa.Column("student_rank", sa.Integer(), nullable=True),
        sa.Column("score_basis", sa.String(length=50), nullable=False),
        sa.Column("ratio", sa.Float(), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=True),
        sa.Column("risk_flags_json", sa.JSON(), nullable=True),
        sa.Column("snapshot_json", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        *_timestamp_columns(),
    )


def downgrade() -> None:
    op.drop_table("recommendation_result")
    op.drop_table("recommendation_scheme")
    op.drop_table("admission_record")
    op.drop_table("college_major")
    op.drop_table("major")
    op.drop_table("college_alias")
    op.drop_table("college")
