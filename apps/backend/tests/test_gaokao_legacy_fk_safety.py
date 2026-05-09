from __future__ import annotations

import importlib.util
from pathlib import Path

from sqlalchemy import create_engine, text


def _load_migration_module():
    script_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "20260508_0031_gaokao_legacy_fk_safety.py"
    )
    spec = importlib.util.spec_from_file_location("gaokao_legacy_fk_safety", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_gaokao_fk_safety_migration_repairs_broken_raw_tables(tmp_path: Path) -> None:
    module = _load_migration_module()
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")

    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.execute(text("CREATE TABLE gaokao_college (id INTEGER PRIMARY KEY, college_name TEXT)"))
        connection.execute(
            text(
                """
                CREATE TABLE gaokao_college_tag (
                    college_id INTEGER NOT NULL,
                    tag_code TEXT,
                    tag_name TEXT NOT NULL,
                    id INTEGER PRIMARY KEY,
                    FOREIGN KEY(college_id) REFERENCES gaokao_college (id) ON DELETE CASCADE
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE data_import_error_log (
                    batch_id INTEGER NOT NULL,
                    row_number INTEGER,
                    field_name TEXT,
                    error_code TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    raw_payload TEXT,
                    id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(batch_id) REFERENCES data_import_batch (id) ON DELETE CASCADE
                )
                """
            )
        )
        connection.execute(text("INSERT INTO gaokao_college (id, college_name) VALUES (1, '有效院校')"))
        connection.execute(
            text(
                """
                INSERT INTO gaokao_college_tag (id, college_id, tag_code, tag_name)
                VALUES (1, 1, 'ok', '有效标签'), (2, 999, 'bad', '悬挂标签')
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO data_import_error_log (
                    id, batch_id, error_code, error_message, created_at, updated_at
                ) VALUES (1, 120, 'IntegrityError', 'legacy orphan', '2026-05-08', '2026-05-08')
                """
            )
        )

    with engine.begin() as connection:
        module._repair_legacy_gaokao_fk_safety(connection)

    with engine.connect() as connection:
        batch_columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(data_import_batch)").fetchall()
        }
        assert {
            "id",
            "batch_code",
            "domain",
            "data_type",
            "province",
            "target_year",
            "source_name",
            "source_title",
            "version_label",
            "status",
            "total_records",
            "started_at",
            "finished_at",
        }.issubset(batch_columns)
        assert connection.scalar(text("SELECT COUNT(*) FROM data_import_error_log")) == 0
        assert connection.scalar(text("SELECT COUNT(*) FROM gaokao_college_tag")) == 1
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
