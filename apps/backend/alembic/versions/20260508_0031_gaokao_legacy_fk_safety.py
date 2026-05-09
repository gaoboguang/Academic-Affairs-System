"""Repair legacy gaokao raw foreign key safety

Revision ID: 20260508_0031
Revises: 20260508_0030
Create Date: 2026-05-08 20:35:00
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy.engine import Connection


revision: str = "20260508_0031"
down_revision: str | None = "20260508_0030"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    _repair_legacy_gaokao_fk_safety(connection)


def downgrade() -> None:
    pass


def _repair_legacy_gaokao_fk_safety(connection: Connection) -> None:
    if _table_exists(connection, "data_import_error_log"):
        connection.exec_driver_sql("DELETE FROM data_import_error_log")

    if not _table_exists(connection, "data_import_batch"):
        connection.exec_driver_sql(
            """
            CREATE TABLE data_import_batch (
                id INTEGER NOT NULL,
                batch_code VARCHAR(64),
                domain VARCHAR(64),
                data_type VARCHAR(64),
                province VARCHAR(50),
                target_year INTEGER,
                source_name VARCHAR(255),
                source_title VARCHAR(255),
                version_label VARCHAR(64),
                status VARCHAR(32),
                total_records INTEGER,
                started_at DATETIME,
                finished_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                PRIMARY KEY (id)
            )
            """
        )
        connection.exec_driver_sql("CREATE INDEX ix_data_import_batch_domain ON data_import_batch (domain)")
        connection.exec_driver_sql("CREATE INDEX ix_data_import_batch_status ON data_import_batch (status)")

    if _table_exists(connection, "gaokao_college_tag") and _table_exists(connection, "gaokao_college"):
        connection.exec_driver_sql(
            """
            DELETE FROM gaokao_college_tag
            WHERE NOT EXISTS (
                SELECT 1
                FROM gaokao_college
                WHERE gaokao_college.id = gaokao_college_tag.college_id
            )
            """
        )


def _table_exists(connection: Connection, table_name: str) -> bool:
    return bool(
        connection.exec_driver_sql(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
    )
