"""Add gaokao pathway schema and rule evaluations

Revision ID: 20260425_0018
Revises: 20260425_0017
Create Date: 2026-04-25 20:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260425_0018"
down_revision: str | None = "20260425_0017"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gaokao_pathway",
        sa.Column("province", sa.String(length=50), server_default="山东", nullable=False),
        sa.Column("pathway_code", sa.String(length=100), nullable=False),
        sa.Column("pathway_name", sa.String(length=120), nullable=False),
        sa.Column("pathway_group", sa.String(length=80), nullable=False),
        sa.Column("student_type", sa.String(length=80), nullable=True),
        sa.Column("exam_type", sa.String(length=80), nullable=True),
        sa.Column("batch_name", sa.String(length=120), nullable=True),
        sa.Column("volunteer_mode", sa.String(length=120), nullable=True),
        sa.Column("max_volunteer_count", sa.Integer(), nullable=True),
        sa.Column("recommendation_depth", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=50), nullable=True),
        sa.Column("notes_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["gaokao_source_document.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("province", "pathway_code", name="uq_gaokao_pathway_code"),
    )
    op.create_index("ix_gaokao_pathway_province_group", "gaokao_pathway", ["province", "pathway_group"])

    op.create_table(
        "gaokao_pathway_rule",
        sa.Column("pathway_id", sa.Integer(), nullable=False),
        sa.Column("rule_code", sa.String(length=120), nullable=False),
        sa.Column("rule_name", sa.String(length=150), nullable=False),
        sa.Column("rule_type", sa.String(length=60), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("condition_json", sa.JSON(), nullable=True),
        sa.Column("message_template", sa.Text(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("manual_review_required", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("valid_from_year", sa.Integer(), nullable=True),
        sa.Column("valid_to_year", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["pathway_id"], ["gaokao_pathway.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["gaokao_source_document.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pathway_id", "rule_code", name="uq_gaokao_pathway_rule_code"),
    )
    op.create_index("ix_gaokao_pathway_rule_type", "gaokao_pathway_rule", ["rule_type", "severity"])

    op.create_table(
        "student_pathway_profile",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("province", sa.String(length=50), server_default="山东", nullable=False),
        sa.Column("candidate_type", sa.String(length=80), nullable=True),
        sa.Column("exam_type", sa.String(length=80), nullable=True),
        sa.Column("subject_combination", sa.String(length=120), nullable=True),
        sa.Column("spring_exam_category", sa.String(length=120), nullable=True),
        sa.Column("art_track", sa.String(length=120), nullable=True),
        sa.Column("sports_track", sa.String(length=120), nullable=True),
        sa.Column("has_gaokao_registration", sa.Boolean(), nullable=True),
        sa.Column("is_fresh_graduate", sa.Boolean(), nullable=True),
        sa.Column("is_vocational_student", sa.Boolean(), nullable=True),
        sa.Column("is_social_candidate", sa.Boolean(), nullable=True),
        sa.Column("has_high_school_equivalent", sa.Boolean(), nullable=True),
        sa.Column("accept_private_college", sa.Boolean(), nullable=True),
        sa.Column("accept_sino_foreign", sa.Boolean(), nullable=True),
        sa.Column("accept_junior_college", sa.Boolean(), nullable=True),
        sa.Column("accept_outside_province", sa.Boolean(), nullable=True),
        sa.Column("accept_early_batch", sa.Boolean(), nullable=True),
        sa.Column("accept_service_commitment", sa.Boolean(), nullable=True),
        sa.Column("accept_interview_or_physical_test", sa.Boolean(), nullable=True),
        sa.Column("career_preferences_json", sa.JSON(), nullable=True),
        sa.Column("region_preferences_json", sa.JSON(), nullable=True),
        sa.Column("family_constraints_json", sa.JSON(), nullable=True),
        sa.Column("known_body_limitations_json", sa.JSON(), nullable=True),
        sa.Column("materials_json", sa.JSON(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "province", name="uq_student_pathway_profile_student_province"),
    )
    op.create_index("ix_student_pathway_profile_candidate", "student_pathway_profile", ["province", "candidate_type"])

    op.create_table(
        "student_pathway_evaluation",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("pathway_id", sa.Integer(), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("status_label", sa.String(length=80), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence_level", sa.String(length=40), nullable=False),
        sa.Column("matched_rules_json", sa.JSON(), nullable=True),
        sa.Column("failed_rules_json", sa.JSON(), nullable=True),
        sa.Column("warning_rules_json", sa.JSON(), nullable=True),
        sa.Column("missing_materials_json", sa.JSON(), nullable=True),
        sa.Column("recommendation_depth", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("next_actions_json", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["pathway_id"], ["gaokao_pathway.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "pathway_id", "target_year", name="uq_student_pathway_evaluation_core"),
    )
    op.create_index("ix_student_pathway_evaluation_status", "student_pathway_evaluation", ["target_year", "status"])


def downgrade() -> None:
    op.drop_index("ix_student_pathway_evaluation_status", table_name="student_pathway_evaluation")
    op.drop_table("student_pathway_evaluation")
    op.drop_index("ix_student_pathway_profile_candidate", table_name="student_pathway_profile")
    op.drop_table("student_pathway_profile")
    op.drop_index("ix_gaokao_pathway_rule_type", table_name="gaokao_pathway_rule")
    op.drop_table("gaokao_pathway_rule")
    op.drop_index("ix_gaokao_pathway_province_group", table_name="gaokao_pathway")
    op.drop_table("gaokao_pathway")
