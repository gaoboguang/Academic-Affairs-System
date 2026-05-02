"""Remove student attendance and behavior records

Revision ID: 20260502_0028
Revises: 20260502_0027
Create Date: 2026-05-02 23:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260502_0028"
down_revision: str | None = "20260502_0027"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM audit_log "
            "WHERE module IN ('attendance', 'behavior') "
            "OR (target_type = 'import_job' AND target_id IN ("
            "SELECT CAST(id AS TEXT) FROM import_job WHERE job_type IN ('attendance', 'behavior')"
            "))"
        )
    )

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "behavior_record" in tables:
        index_names = {item["name"] for item in inspector.get_indexes("behavior_record")}
        if "ix_behavior_record_student_date" in index_names:
            op.drop_index("ix_behavior_record_student_date", table_name="behavior_record")
        op.drop_table("behavior_record")
    if "attendance_record" in tables:
        index_names = {item["name"] for item in inspector.get_indexes("attendance_record")}
        if "ix_attendance_record_scope_date" in index_names:
            op.drop_index("ix_attendance_record_scope_date", table_name="attendance_record")
        op.drop_table("attendance_record")
    bind.execute(sa.text("DELETE FROM import_job WHERE job_type IN ('attendance', 'behavior')"))


def downgrade() -> None:
    op.create_table(
        "attendance_record",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("scope", sa.String(length=20), server_default="day", nullable=False),
        sa.Column("period_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source_batch_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["source_batch_id"], ["import_job.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "record_date",
            "scope",
            "period_index",
            name="uq_attendance_record_student_date_scope_period",
        ),
    )
    op.create_index(
        "ix_attendance_record_scope_date",
        "attendance_record",
        ["record_date", "student_id", "status"],
    )
    op.create_table(
        "behavior_record",
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="中", nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("handler_name", sa.String(length=100), nullable=True),
        sa.Column("points_delta", sa.Float(), nullable=True),
        sa.Column("attachment_path", sa.String(length=255), nullable=True),
        sa.Column("source_batch_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["source_batch_id"], ["import_job.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_behavior_record_student_date",
        "behavior_record",
        ["student_id", "record_date", "category"],
    )
