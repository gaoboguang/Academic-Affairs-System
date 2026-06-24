"""Add art volunteer profile fields

Revision ID: 20260510_0032
Revises: 20260508_0031
Create Date: 2026-05-10 23:10:00
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy.engine import Connection


revision: str = "20260510_0032"
down_revision: str | None = "20260508_0031"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()
    _add_column_if_missing(connection, "student_pathway_profile", "art_professional_score", "FLOAT")
    _add_column_if_missing(connection, "student_pathway_profile", "art_professional_full_score", "FLOAT")
    _add_column_if_missing(connection, "student_pathway_profile", "art_score_source", "VARCHAR(150)")
    _add_column_if_missing(connection, "student_pathway_profile", "art_score_note", "TEXT")
    _add_column_if_missing(connection, "volunteer_draft", "art_track", "VARCHAR(120)")


def downgrade() -> None:
    pass


def _add_column_if_missing(connection: Connection, table_name: str, column_name: str, column_type: str) -> None:
    if not _table_exists(connection, table_name):
        return
    if column_name in _table_columns(connection, table_name):
        return
    connection.exec_driver_sql(f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}')


def _table_exists(connection: Connection, table_name: str) -> bool:
    return bool(
        connection.exec_driver_sql(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
    )


def _table_columns(connection: Connection, table_name: str) -> set[str]:
    return {
        str(row[1])
        for row in connection.exec_driver_sql(f'PRAGMA table_info("{table_name}")').fetchall()
    }
