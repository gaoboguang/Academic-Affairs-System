"""Add gaokao source document and import run tables

Revision ID: 20260425_0016
Revises: 20260424_0015
Create Date: 2026-04-25 11:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260425_0016"
down_revision: str | None = "20260424_0015"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


TRACKED_DATA_TABLES = (
    "admission_record",
    "enrollment_plan",
    "score_rank_segment",
    "gaokao_score_line",
    "gaokao_admission_result",
    "gaokao_admission_plan",
    "gaokao_subject_requirement",
    "gaokao_college_chapter_rule",
)


def upgrade() -> None:
    op.create_table(
        "gaokao_source_document",
        sa.Column("province", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("official_org", sa.String(length=150), nullable=False),
        sa.Column("source_registry_code", sa.String(length=64), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("local_file_path", sa.Text(), nullable=True),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column("parser_name", sa.String(length=128), nullable=True),
        sa.Column("parser_version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="registered", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "province",
            "year",
            "source_type",
            "url",
            name="uq_gaokao_source_document_url",
        ),
    )
    op.create_index("ix_gaokao_source_document_province_year", "gaokao_source_document", ["province", "year"])
    op.create_index("ix_gaokao_source_document_source_type", "gaokao_source_document", ["source_type"])
    op.create_index("ix_gaokao_source_document_status", "gaokao_source_document", ["status"])
    op.create_index("ix_gaokao_source_document_registry_code", "gaokao_source_document", ["source_registry_code"])

    op.create_table(
        "gaokao_import_run",
        sa.Column("source_document_id", sa.Integer(), nullable=False),
        sa.Column("importer_name", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("total_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("success_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_rows", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_report_path", sa.Text(), nullable=True),
        sa.Column("raw_snapshot_path", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["gaokao_source_document.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gaokao_import_run_source_document_id", "gaokao_import_run", ["source_document_id"])
    op.create_index("ix_gaokao_import_run_importer_name", "gaokao_import_run", ["importer_name"])
    op.create_index("ix_gaokao_import_run_status", "gaokao_import_run", ["status"])

    for table_name in TRACKED_DATA_TABLES:
        _add_tracking_column_if_possible(table_name, "source_document_id")
        _add_tracking_column_if_possible(table_name, "import_run_id")


def downgrade() -> None:
    for table_name in reversed(TRACKED_DATA_TABLES):
        _drop_tracking_column_if_possible(table_name, "import_run_id")
        _drop_tracking_column_if_possible(table_name, "source_document_id")

    op.drop_index("ix_gaokao_import_run_status", table_name="gaokao_import_run")
    op.drop_index("ix_gaokao_import_run_importer_name", table_name="gaokao_import_run")
    op.drop_index("ix_gaokao_import_run_source_document_id", table_name="gaokao_import_run")
    op.drop_table("gaokao_import_run")

    op.drop_index("ix_gaokao_source_document_registry_code", table_name="gaokao_source_document")
    op.drop_index("ix_gaokao_source_document_status", table_name="gaokao_source_document")
    op.drop_index("ix_gaokao_source_document_source_type", table_name="gaokao_source_document")
    op.drop_index("ix_gaokao_source_document_province_year", table_name="gaokao_source_document")
    op.drop_table("gaokao_source_document")


def _add_tracking_column_if_possible(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in existing:
        return
    op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True))


def _drop_tracking_column_if_possible(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(table_name):
        return
    existing = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name not in existing:
        return
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.drop_column(column_name)
