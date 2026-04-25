from __future__ import annotations

from pathlib import Path

from sqlalchemy import func, select

from app.models import GaokaoImportRun, GaokaoSourceDocument
from app.services.gaokao_imports import (
    DEFAULT_SOURCE_DOCUMENT_SEEDS,
    register_gaokao_local_file,
    seed_default_gaokao_sources,
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
        assert "等待 B1" in (saved_run.note or "")


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
