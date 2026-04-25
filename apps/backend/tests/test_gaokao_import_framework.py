from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy import text

from app.models import GaokaoImportRun, GaokaoSourceDocument
from app.services.gaokao_imports import (
    DEFAULT_SOURCE_DOCUMENT_SEEDS,
    register_gaokao_local_file,
    seed_default_gaokao_sources,
)
from app.services.gaokao_official_importers import (
    build_b1_coverage,
    import_b1_shandong_core,
    import_registered_gaokao_file,
)


def test_seed_default_gaokao_sources_creates_documents_and_directories(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        result = seed_default_gaokao_sources(session, test_settings)
        first_count = session.scalar(select(func.count()).select_from(GaokaoSourceDocument))
        second_result = seed_default_gaokao_sources(session, test_settings)
        second_count = session.scalar(select(func.count()).select_from(GaokaoSourceDocument))

    assert result["source_documents_upserted"] == len(DEFAULT_SOURCE_DOCUMENT_SEEDS)
    assert result["source_documents_created"] == len(DEFAULT_SOURCE_DOCUMENT_SEEDS)
    assert second_result["source_documents_created"] == 0
    assert first_count == len(DEFAULT_SOURCE_DOCUMENT_SEEDS)
    assert second_count == len(DEFAULT_SOURCE_DOCUMENT_SEEDS)
    assert (test_settings.data_dir / "imports" / "gaokao" / "official").is_dir()
    assert (test_settings.data_dir / "imports" / "gaokao" / "manual").is_dir()


def test_register_gaokao_local_file_updates_document_and_creates_pending_run(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        seed_default_gaokao_sources(session, test_settings)
        document = session.scalar(
            select(GaokaoSourceDocument).where(
                GaokaoSourceDocument.year == 2023,
                GaokaoSourceDocument.source_type == "score_rank_segment",
            )
        )
        assert document is not None
        source_document_id = document.id

    local_file = test_settings.data_dir / "imports" / "gaokao" / "official" / "2023" / "score-rank.xls"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"official-file")

    with app.state.db.session_scope() as session:
        document, run = register_gaokao_local_file(
            session,
            test_settings,
            source_document_id=source_document_id,
            file_path=local_file,
            importer_name="shandong_score_rank_segment",
        )
        run_id = run.id
        assert document.status == "file_ready"
        assert document.local_file_path == str(local_file)
        assert document.file_sha256 is not None
        assert run.status == "pending"
        assert run.total_rows == 0
        assert run.success_rows == 0
        assert run.raw_snapshot_path == document.local_file_path

    with app.state.db.session_scope() as session:
        saved_run = session.get(GaokaoImportRun, run_id)
        assert saved_run is not None
        assert saved_run.importer_name == "shandong_score_rank_segment"
        assert "等待对应解析器" in (saved_run.note or "")


def test_register_gaokao_local_file_rejects_files_outside_import_dirs(app, test_settings, tmp_path: Path) -> None:
    with app.state.db.session_scope() as session:
        seed_default_gaokao_sources(session, test_settings)
        document_id = session.scalar(select(GaokaoSourceDocument.id))

    outside_file = tmp_path / "outside.xls"
    outside_file.write_bytes(b"outside")

    with app.state.db.session_scope() as session:
        try:
            register_gaokao_local_file(
                session,
                test_settings,
                source_document_id=document_id,
                file_path=outside_file,
                importer_name="shandong_score_line",
            )
        except ValueError as exc:
            assert "data/imports/gaokao/official" in str(exc)
        else:
            raise AssertionError("outside files must be rejected")


def test_import_score_rank_file_writes_segments_and_updates_run(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        seed_default_gaokao_sources(session, test_settings)
        document = session.scalar(
            select(GaokaoSourceDocument).where(
                GaokaoSourceDocument.year == 2023,
                GaokaoSourceDocument.source_type == "score_rank_segment",
            )
        )
        assert document is not None
        source_document_id = document.id

    local_file = test_settings.data_dir / "imports" / "gaokao" / "official" / "2023" / "score-rank.xls"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text(
        """
        <table>
          <tr><td>2023年夏季高考文化成绩一分一段表</td></tr>
          <tr><td>分数段</td><td>全体</td><td></td><td>选考物理</td><td></td></tr>
          <tr><td></td><td>本段人数</td><td>累计人数</td><td>本段人数</td><td>累计人数</td></tr>
          <tr><td>697</td><td>14</td><td>62</td><td>14</td><td>62</td></tr>
          <tr><td>696</td><td>9</td><td>71</td><td>9</td><td>71</td></tr>
        </table>
        """,
        encoding="utf-8",
    )

    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        _document, run = register_gaokao_local_file(
            session,
            test_settings,
            source_document_id=source_document_id,
            file_path=local_file,
            importer_name="shandong_score_rank_segment",
        )
        stats = import_registered_gaokao_file(session, test_settings, import_run_id=run.id)
        saved_run = session.get(GaokaoImportRun, run.id)
        count_with_source = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM score_rank_segment
                WHERE year = 2023 AND source_document_id = :source_document_id AND import_run_id = :import_run_id
                """
            ),
            {"source_document_id": source_document_id, "import_run_id": run.id},
        )

    assert stats.success_rows == 4
    assert stats.failed_rows == 0
    assert saved_run is not None
    assert saved_run.status == "success"
    assert count_with_source == 4


def test_b1_core_import_uses_existing_local_file_without_download(app, test_settings, tmp_path: Path) -> None:
    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        seed_default_gaokao_sources(session, test_settings)

    local_file = (
        test_settings.data_dir
        / "imports"
        / "gaokao"
        / "official"
        / "2023"
        / "2023_score_rank_segment_fixture.xls"
    )
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text(
        """
        <table>
          <tr><td>2023年夏季高考文化成绩一分一段表</td></tr>
          <tr><td>分数段</td><td>全体</td><td></td></tr>
          <tr><td></td><td>本段人数</td><td>累计人数</td></tr>
          <tr><td>697</td><td>14</td><td>62</td></tr>
        </table>
        """,
        encoding="utf-8",
    )

    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        payload = import_b1_shandong_core(
            session,
            test_settings,
            download_missing=False,
            years=(2023,),
            source_types=("score_rank_segment",),
            coverage_doc=tmp_path / "coverage.md",
        )
        document = session.scalar(
            select(GaokaoSourceDocument).where(
                GaokaoSourceDocument.year == 2023,
                GaokaoSourceDocument.source_type == "score_rank_segment",
            )
        )
        assert document is not None
        count_with_source = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM score_rank_segment
                WHERE year = 2023 AND source_document_id = :source_document_id
                """
            ),
            {"source_document_id": document.id},
        )

    assert payload["imports"][0]["success_rows"] == 1
    assert document.local_file_path.endswith("2023_score_rank_segment_fixture.xls")
    assert count_with_source == 1


def test_import_admission_file_updates_raw_and_application_records(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        seed_default_gaokao_sources(session, test_settings)
        document = session.scalar(
            select(GaokaoSourceDocument).where(
                GaokaoSourceDocument.year == 2023,
                GaokaoSourceDocument.source_type == "admission_result",
            )
        )
        assert document is not None
        source_document_id = document.id

    local_file = test_settings.data_dir / "imports" / "gaokao" / "official" / "2023" / "admission.xls"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_text(
        """
        <table>
          <tr><td>山东省2023年普通类常规批第1次志愿投档情况表</td></tr>
          <tr><td>专业</td><td>院校</td><td>投档计划数</td><td>投档最低位次</td></tr>
          <tr><td>16文科试验班类</td><td>A001北京大学</td><td>25</td><td>181</td></tr>
        </table>
        """,
        encoding="utf-8",
    )

    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        _document, run = register_gaokao_local_file(
            session,
            test_settings,
            source_document_id=source_document_id,
            file_path=local_file,
            importer_name="shandong_admission_result",
        )
        stats = import_registered_gaokao_file(session, test_settings, import_run_id=run.id)
        raw_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM gaokao_admission_result
                WHERE year = 2023 AND source_document_id = :source_document_id AND import_run_id = :import_run_id
                """
            ),
            {"source_document_id": source_document_id, "import_run_id": run.id},
        )
        app_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM admission_record
                WHERE year = 2023 AND source_document_id = :source_document_id AND import_run_id = :import_run_id
                """
            ),
            {"source_document_id": source_document_id, "import_run_id": run.id},
        )

    assert stats.success_rows == 1
    assert stats.failed_rows == 0
    assert raw_count == 1
    assert app_count == 1


def test_import_score_line_file_writes_official_lines(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        seed_default_gaokao_sources(session, test_settings)
        document = session.scalar(
            select(GaokaoSourceDocument).where(
                GaokaoSourceDocument.year == 2023,
                GaokaoSourceDocument.source_type == "score_line",
            )
        )
        assert document is not None
        source_document_id = document.id

    local_file = test_settings.data_dir / "imports" / "gaokao" / "official" / "2023" / "score-line.png"
    local_file.parent.mkdir(parents=True, exist_ok=True)
    local_file.write_bytes(b"fake-official-image")

    with app.state.db.session_scope() as session:
        _create_b1_raw_tables(session)
        _document, run = register_gaokao_local_file(
            session,
            test_settings,
            source_document_id=source_document_id,
            file_path=local_file,
            importer_name="shandong_score_line",
        )
        stats = import_registered_gaokao_file(session, test_settings, import_run_id=run.id)
        coverage = build_b1_coverage(session)
        line_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM gaokao_score_line
                WHERE year = 2023 AND source_document_id = :source_document_id
                """
            ),
            {"source_document_id": source_document_id},
        )

    assert stats.success_rows == 15
    assert stats.failed_rows == 0
    assert line_count == 15
    assert coverage["years"][2023]["score_line_with_source"] == 15


def _create_b1_raw_tables(session) -> None:
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS score_rank_segment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT NOT NULL,
                year INTEGER NOT NULL,
                score_type TEXT,
                subject_group TEXT,
                score NUMERIC,
                segment_count INTEGER,
                cumulative_count INTEGER,
                rank_value INTEGER,
                created_at TEXT,
                updated_at TEXT,
                source_level TEXT,
                source_title TEXT,
                source_url TEXT,
                local_source_path TEXT,
                parser_script_name TEXT,
                published_at TEXT,
                review_status TEXT,
                source_record_hash TEXT,
                data_version_label TEXT,
                source_document_id INTEGER,
                import_run_id INTEGER
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gaokao_admission_result (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT NOT NULL,
                year INTEGER NOT NULL,
                candidate_type TEXT,
                batch_name TEXT,
                round_no TEXT,
                college_code_snapshot TEXT,
                college_name_snapshot TEXT,
                major_code_snapshot TEXT,
                major_name_snapshot TEXT,
                min_score NUMERIC,
                min_rank INTEGER,
                plan_count INTEGER,
                original_min_rank_text TEXT,
                remark TEXT,
                created_at TEXT,
                updated_at TEXT,
                source_level TEXT,
                source_title TEXT,
                source_url TEXT,
                local_source_path TEXT,
                parser_script_name TEXT,
                published_at TEXT,
                review_status TEXT,
                source_record_hash TEXT,
                data_version_label TEXT,
                source_document_id INTEGER,
                import_run_id INTEGER
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS gaokao_score_line (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                province TEXT NOT NULL,
                year INTEGER NOT NULL,
                candidate_type TEXT,
                batch_name TEXT,
                line_type TEXT,
                score NUMERIC,
                remark TEXT,
                created_at TEXT,
                updated_at TEXT,
                source_level TEXT,
                source_title TEXT,
                source_url TEXT,
                local_source_path TEXT,
                parser_script_name TEXT,
                published_at TEXT,
                review_status TEXT,
                source_record_hash TEXT,
                data_version_label TEXT,
                source_document_id INTEGER,
                import_run_id INTEGER
            )
            """
        )
    )
