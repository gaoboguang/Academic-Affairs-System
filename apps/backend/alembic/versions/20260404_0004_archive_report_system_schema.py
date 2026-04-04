"""Growth archive, reports, and backup schema

Revision ID: 20260404_0004
Revises: 20260403_0003
Create Date: 2026-04-04 10:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260404_0004"
down_revision: str | None = "20260403_0003"
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
        "stored_file",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "student_growth_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("owner_name", sa.String(length=100), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "student_growth_attachment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("record_id", sa.Integer(), sa.ForeignKey("student_growth_record.id"), nullable=False),
        sa.Column("stored_file_id", sa.Integer(), sa.ForeignKey("stored_file.id"), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "backup_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backup_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "report_export_record",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("report_name", sa.String(length=100), nullable=False),
        sa.Column("params_json", sa.JSON(), nullable=True),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("exported_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        *_timestamp_columns(),
    )


def downgrade() -> None:
    op.drop_table("report_export_record")
    op.drop_table("backup_record")
    op.drop_table("student_growth_attachment")
    op.drop_table("student_growth_record")
    op.drop_table("stored_file")
