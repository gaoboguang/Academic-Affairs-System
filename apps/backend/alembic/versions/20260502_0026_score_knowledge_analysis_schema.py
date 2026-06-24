"""Add score knowledge analysis schema

Revision ID: 20260502_0026
Revises: 20260502_0025
Create Date: 2026-05-02 15:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260502_0026"
down_revision: str | None = "20260502_0025"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "score_question_import_batch",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("import_time", sa.DateTime(timezone=False), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("success_rows", sa.Integer(), nullable=False),
        sa.Column("failed_rows", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_report_path", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_score_question_import_batch_exam_id", "score_question_import_batch", ["exam_id"])

    op.create_table(
        "knowledge_point",
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_id", "name", name="uq_knowledge_point_subject_name"),
    )
    op.create_index("ix_knowledge_point_subject_id", "knowledge_point", ["subject_id"])

    op.create_table(
        "score_question",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("question_no", sa.String(length=50), nullable=False),
        sa.Column("full_score", sa.Float(), nullable=False),
        sa.Column("question_type", sa.String(length=50), nullable=True),
        sa.Column("ability_level", sa.String(length=80), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "subject_id", "question_no", name="uq_score_question"),
    )
    op.create_index("ix_score_question_exam_subject", "score_question", ["exam_id", "subject_id"])

    op.create_table(
        "score_question_knowledge_point",
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("knowledge_point_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["knowledge_point_id"], ["knowledge_point.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["score_question.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("question_id", "knowledge_point_id", name="uq_score_question_knowledge_point"),
    )
    op.create_index("ix_score_question_knowledge_question", "score_question_knowledge_point", ["question_id"])
    op.create_index("ix_score_question_knowledge_point", "score_question_knowledge_point", ["knowledge_point_id"])

    op.create_table(
        "score_question_record",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("score_status", sa.String(length=30), nullable=False),
        sa.Column("raw_text", sa.String(length=100), nullable=True),
        sa.Column("import_batch_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.ForeignKeyConstraint(["import_batch_id"], ["score_question_import_batch.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["score_question.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "student_id", "question_id", name="uq_score_question_record"),
    )
    op.create_index("ix_score_question_record_exam_student", "score_question_record", ["exam_id", "student_id"])
    op.create_index("ix_score_question_record_exam_subject", "score_question_record", ["exam_id", "subject_id"])

    op.create_table(
        "score_knowledge_snapshot",
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("knowledge_point_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("full_score", sa.Float(), nullable=False),
        sa.Column("score_rate", sa.Float(), nullable=True),
        sa.Column("grade_average_rate", sa.Float(), nullable=True),
        sa.Column("grade_gap_rate", sa.Float(), nullable=True),
        sa.Column("lost_score", sa.Float(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("question_numbers_json", sa.JSON(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column("diagnosis_label", sa.String(length=50), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("rebuilt_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"]),
        sa.ForeignKeyConstraint(["knowledge_point_id"], ["knowledge_point.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exam_id",
            "student_id",
            "subject_id",
            "knowledge_point_id",
            name="uq_score_knowledge_snapshot",
        ),
    )
    op.create_index("ix_score_knowledge_snapshot_exam_student", "score_knowledge_snapshot", ["exam_id", "student_id"])
    op.create_index("ix_score_knowledge_snapshot_priority", "score_knowledge_snapshot", ["exam_id", "student_id", "priority_score"])


def downgrade() -> None:
    op.drop_index("ix_score_knowledge_snapshot_priority", table_name="score_knowledge_snapshot")
    op.drop_index("ix_score_knowledge_snapshot_exam_student", table_name="score_knowledge_snapshot")
    op.drop_table("score_knowledge_snapshot")
    op.drop_index("ix_score_question_record_exam_subject", table_name="score_question_record")
    op.drop_index("ix_score_question_record_exam_student", table_name="score_question_record")
    op.drop_table("score_question_record")
    op.drop_index("ix_score_question_knowledge_point", table_name="score_question_knowledge_point")
    op.drop_index("ix_score_question_knowledge_question", table_name="score_question_knowledge_point")
    op.drop_table("score_question_knowledge_point")
    op.drop_index("ix_score_question_exam_subject", table_name="score_question")
    op.drop_table("score_question")
    op.drop_index("ix_knowledge_point_subject_id", table_name="knowledge_point")
    op.drop_table("knowledge_point")
    op.drop_index("ix_score_question_import_batch_exam_id", table_name="score_question_import_batch")
    op.drop_table("score_question_import_batch")
