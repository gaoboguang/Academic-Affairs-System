from __future__ import annotations

import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings
from app.main import create_app
from app.models import (
    AdmissionRecord,
    College,
    EnrollmentPlan,
    ImportJob,
    Major,
    ProvinceVolunteerRule,
)
from app.models import Base


def test_gaokao_data_overview_falls_back_to_sync_board_baseline(client) -> None:
    response = client.get("/api/gaokao/data-overview")
    assert response.status_code == 200
    payload = response.json()

    assert payload["source_mode"] == "doc_baseline"
    assert payload["data_version"] == "DB RC1"
    assert payload["school_total"] == 3344
    assert payload["recruit_site_covered"] == 1813
    assert payload["chapter_url_covered"] == 172
    assert payload["duplicate_group_total"] == 4
    assert payload["same_name_cross_site_group_total"] == 2


def test_gaokao_data_health_endpoint_returns_p0_summary(client) -> None:
    response = client.get("/api/gaokao/data-health")
    assert response.status_code == 200
    payload = response.json()

    assert payload["exists"] is True
    assert payload["province"] == "山东"
    assert "P0 缺口" in payload["summary"]
    assert any(item["key"] == "enrollment_plan" for item in payload["coverage"])
    assert any(item["key"] == "admission_record" for item in payload["tables"])


def test_gaokao_data_overview_uses_separate_gaokao_db_when_configured(tmp_path) -> None:
    data_dir = tmp_path / "data"
    gaokao_db_path = data_dir / "local_edu_tool" / "local_edu.sqlite3"
    gaokao_db_path.parent.mkdir(parents=True, exist_ok=True)
    gaokao_db_path.touch()

    settings = Settings(
        data_dir=data_dir,
        db_path=data_dir / "app.db",
        gaokao_db_path=gaokao_db_path,
        allowed_origins=["http://127.0.0.1:5173"],
        debug=False,
    )
    app = create_app(settings)
    ensure_runtime_directories(settings)
    Base.metadata.create_all(app.state.db.engine)

    assert app.state.gaokao_db is not None
    with app.state.gaokao_db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    name TEXT,
                    province TEXT,
                    recruit_site TEXT,
                    duplicate_group_key TEXT,
                    same_name_group_key TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_policy_reference (
                    id INTEGER PRIMARY KEY,
                    college_id INTEGER,
                    chapter_url TEXT,
                    fallback_url TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, name, province, recruit_site,
                    duplicate_group_key, same_name_group_key, updated_at
                ) VALUES
                    (201, 'GK201', '独立高考库学校', '山东', 'https://recruit.example/201', 'dup-201', 'same-201', '2026-04-21 14:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_policy_reference (id, college_id, chapter_url, fallback_url, updated_at)
                VALUES (1, 201, 'https://chapter.example/201', 'https://fallback.example/201', '2026-04-21 14:30:00')
                """
            )
        )

    try:
        with TestClient(app) as client:
            response = client.get("/api/gaokao/data-overview")
            assert response.status_code == 200
            payload = response.json()
            assert payload["source_mode"] == "db_rc1_live"
            assert payload["school_total"] == 1
            assert payload["recruit_site_covered"] == 1
            assert payload["chapter_url_covered"] == 1
            assert payload["fallback_url_covered"] == 1

            options_response = client.get("/api/gaokao/college-options", params={"q": "独立高考库"})
            assert options_response.status_code == 200
            options_payload = options_response.json()
            assert len(options_payload) == 1
            assert options_payload[0]["college_id"] == 201
            assert options_payload[0]["source_mode"] == "db_rc1_live"
    finally:
        app.state.db.dispose()
        if app.state.gaokao_db is not None:
            app.state.gaokao_db.dispose()


def test_create_app_prefers_embedded_gaokao_tables_over_external_snapshot(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    app_db_path = data_dir / "app.db"
    gaokao_db_path = data_dir / "local_edu_tool" / "local_edu.sqlite3"
    gaokao_db_path.parent.mkdir(parents=True, exist_ok=True)
    gaokao_db_path.touch()

    with sqlite3.connect(app_db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gaokao_college (
                id INTEGER PRIMARY KEY,
                college_code TEXT,
                name TEXT,
                province TEXT,
                recruit_site TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO gaokao_college (
                id, college_code, name, province, recruit_site, updated_at
            ) VALUES
                (301, 'GK301', '嵌入式高考表学校', '山东', 'https://recruit.example/301', '2026-04-22 16:10:00')
            """
        )

    settings = Settings(
        data_dir=data_dir,
        db_path=app_db_path,
        gaokao_db_path=gaokao_db_path,
        allowed_origins=["http://127.0.0.1:5173"],
        debug=False,
    )
    app = create_app(settings)
    ensure_runtime_directories(settings)
    Base.metadata.create_all(app.state.db.engine)

    assert app.state.gaokao_db is None

    try:
        with TestClient(app) as client:
            response = client.get("/api/gaokao/data-overview")
            assert response.status_code == 200
            payload = response.json()
            assert payload["source_mode"] == "db_rc1_live"
            assert payload["school_total"] == 1
            assert payload["recruit_site_covered"] == 1
    finally:
        app.state.db.dispose()


def test_gaokao_data_overview_marks_app_tables_partial_when_raw_tables_have_data(tmp_path) -> None:
    data_dir = tmp_path / "data"
    gaokao_db_path = data_dir / "local_edu_tool" / "local_edu.sqlite3"
    gaokao_db_path.parent.mkdir(parents=True, exist_ok=True)
    gaokao_db_path.touch()

    settings = Settings(
        data_dir=data_dir,
        db_path=data_dir / "app.db",
        gaokao_db_path=gaokao_db_path,
        allowed_origins=["http://127.0.0.1:5173"],
        debug=False,
    )
    app = create_app(settings)
    ensure_runtime_directories(settings)
    Base.metadata.create_all(app.state.db.engine)

    assert app.state.gaokao_db is not None
    with app.state.gaokao_db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    name TEXT,
                    province TEXT,
                    recruit_site TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_admission_plan (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_admission_result (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, name, province, recruit_site, updated_at
                ) VALUES
                    (201, 'GK201', '独立高考库学校', '山东', 'https://recruit.example/201', '2026-04-21 14:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_admission_plan (id, province, updated_at) VALUES
                    (1, '山东', '2026-04-21 14:10:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_admission_result (id, province, updated_at) VALUES
                    (1, '山东', '2026-04-21 14:20:00')
                """
            )
        )

    try:
        with TestClient(app) as client:
            response = client.get("/api/gaokao/data-overview")
            assert response.status_code == 200
            payload = response.json()
            table_map = {item["key"]: item for item in payload["core_tables"]}

            assert table_map["enrollment_plan"]["record_total"] == 0
            assert table_map["enrollment_plan"]["status"] == "partial"
            assert any("gaokao_admission_plan 已有 1 条原始记录" in note for note in table_map["enrollment_plan"]["notes"])

            assert table_map["admission_record"]["record_total"] == 0
            assert table_map["admission_record"]["status"] == "partial"
            assert any(
                "gaokao_admission_result 已有 1 条原始记录" in note
                for note in table_map["admission_record"]["notes"]
            )
    finally:
        app.state.db.dispose()
        if app.state.gaokao_db is not None:
            app.state.gaokao_db.dispose()


def test_gaokao_review_summary_and_evidence_use_live_rc1_tables(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    name TEXT,
                    province TEXT,
                    official_site TEXT,
                    recruit_site TEXT,
                    review_status TEXT,
                    retrieval_status TEXT,
                    source_url TEXT,
                    source_title TEXT,
                    duplicate_group_key TEXT,
                    same_name_group_key TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_policy_reference (
                    id INTEGER PRIMARY KEY,
                    college_id INTEGER,
                    chapter_url TEXT,
                    fallback_url TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, name, province, official_site, recruit_site,
                    review_status, retrieval_status, source_url, source_title,
                    duplicate_group_key, same_name_group_key, updated_at
                ) VALUES
                    (101, 'SD001', '山东示例大学', '山东', 'https://official.example/sd', 'https://recruit.example/sd',
                     'pending_manual_review', 'retrieved', 'https://source.example/sd', '山东来源',
                     'dup-1', 'same-1', '2026-04-16 09:00:00'),
                    (102, 'SD002', '山东示例学院', '山东', NULL, NULL,
                     'unresolved', 'pending', NULL, NULL,
                     'dup-1', NULL, '2026-04-16 08:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_policy_reference (id, college_id, chapter_url, fallback_url, updated_at)
                VALUES (1, 101, 'https://chapter.example/sd', 'https://fallback.example/sd', '2026-04-16 09:30:00')
                """
            )
        )

    overview_response = client.get("/api/gaokao/data-overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["source_mode"] == "db_rc1_live"
    assert overview_payload["school_total"] == 2
    assert overview_payload["recruit_site_covered"] == 1
    assert overview_payload["chapter_url_covered"] == 1
    assert overview_payload["fallback_url_covered"] == 1
    assert overview_payload["duplicate_group_total"] == 1
    assert overview_payload["same_name_cross_site_group_total"] == 1

    review_response = client.get(
        "/api/gaokao/review-summary",
        params={"status": "pending_manual_review", "keyword": "山东"},
    )
    assert review_response.status_code == 200
    review_payload = review_response.json()
    assert review_payload["source_available"] is True
    assert review_payload["active_filter"] == "pending_manual_review"
    assert review_payload["active_keyword"] == "山东"
    assert review_payload["matched_total"] == 1
    assert review_payload["counts"][0]["count"] == 1
    assert review_payload["items"][0]["college_id"] == 101
    assert review_payload["items"][0]["chapter_url"] == "https://chapter.example/sd"
    assert review_payload["duplicate_groups"][0]["item_count"] == 2
    assert review_payload["duplicate_groups"][0]["priority_code"] == "high"
    assert review_payload["duplicate_groups"][0]["unresolved_total"] == 1
    assert "证据链" in review_payload["duplicate_groups"][0]["suggested_action"]
    compare_field_map = {
        item["key"]: item
        for item in review_payload["duplicate_groups"][0]["comparison_fields"]
    }
    assert compare_field_map["province"]["status"] == "same"
    assert compare_field_map["college_code"]["status"] == "mixed"
    assert compare_field_map["official_site"]["status"] == "partial"
    assert compare_field_map["recruit_site"]["missing_total"] == 1
    assert compare_field_map["effective_chapter_url"]["missing_total"] == 1
    assert compare_field_map["source_title"]["status"] == "partial"
    assert compare_field_map["source_url"]["status"] == "partial"
    duplicate_member_ids = {
        item["college_id"]
        for item in review_payload["duplicate_groups"][0]["member_items"]
    }
    assert duplicate_member_ids == {101, 102}
    duplicate_member_map = {
        item["college_id"]: item
        for item in review_payload["duplicate_groups"][0]["member_items"]
    }
    assert duplicate_member_map[101]["effective_chapter_url"] == "https://chapter.example/sd"
    assert duplicate_member_map[101]["source_url"] == "https://source.example/sd"
    assert review_payload["priority_groups"][0]["key"] == "dup-1"
    assert any("命中 1 所学校" in item for item in review_payload["highlights"])

    evidence_response = client.get("/api/gaokao/college-evidence/101")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    assert evidence_payload["source_available"] is True
    assert evidence_payload["college_name"] == "山东示例大学"
    assert evidence_payload["official_site"] == "https://official.example/sd"
    assert evidence_payload["chapter_url"] == "https://chapter.example/sd"
    assert evidence_payload["review_status"] == "pending_manual_review"


def test_gaokao_review_summary_supports_priority_sort_and_focus_filters(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    name TEXT,
                    province TEXT,
                    official_site TEXT,
                    recruit_site TEXT,
                    review_status TEXT,
                    retrieval_status TEXT,
                    source_url TEXT,
                    source_title TEXT,
                    duplicate_group_key TEXT,
                    same_name_group_key TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_policy_reference (
                    id INTEGER PRIMARY KEY,
                    college_id INTEGER,
                    chapter_url TEXT,
                    fallback_url TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, name, province, official_site, recruit_site,
                    review_status, retrieval_status, source_url, source_title,
                    duplicate_group_key, same_name_group_key, updated_at
                ) VALUES
                    (101, 'SD101', '山东普通队列大学', '山东', 'https://official.example/101', 'https://recruit.example/101',
                     'pending_manual_review', 'retrieved', 'https://source.example/101', '山东来源 101',
                     NULL, NULL, '2026-04-16 09:00:00'),
                    (102, 'SD102', '山东高优先大学', '山东', NULL, NULL,
                     'unresolved', 'pending', 'https://source.example/102', '山东来源 102',
                     'dup-urgent', NULL, '2026-04-16 10:00:00'),
                    (103, 'SD103', '山东待确认学院', '山东', 'https://official.example/103', 'https://recruit.example/103',
                     'pending_manual_review_with_official_candidate', 'retrieved', 'https://source.example/103', '山东来源 103',
                     NULL, 'same-103', '2026-04-16 08:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_policy_reference (id, college_id, chapter_url, fallback_url, updated_at)
                VALUES (1, 101, 'https://chapter.example/101', NULL, '2026-04-16 09:30:00')
                """
            )
        )

    default_response = client.get("/api/gaokao/review-summary")
    assert default_response.status_code == 200
    default_payload = default_response.json()
    quick_filter_map = {item["code"]: item for item in default_payload["quick_filters"]}

    assert default_payload["active_focus"] == "all"
    assert default_payload["active_sort"] == "priority_desc"
    assert default_payload["queue_total"] == 3
    assert [item["college_id"] for item in default_payload["items"][:3]] == [102, 103, 101]
    assert default_payload["items"][0]["priority_code"] == "high"
    assert "缺章程入口" in default_payload["items"][0]["priority_reasons"]
    assert [item["key"] for item in default_payload["priority_groups"][:2]] == ["dup-urgent", "same-103"]
    assert default_payload["priority_groups"][0]["group_type"] == "duplicate"
    assert default_payload["priority_groups"][0]["high_priority_member_total"] == 1
    assert default_payload["priority_groups"][0]["missing_recruit_site_total"] == 1
    priority_compare_field_map = {
        item["key"]: item
        for item in default_payload["priority_groups"][0]["comparison_fields"]
    }
    assert priority_compare_field_map["province"]["title"] == "省份"
    assert priority_compare_field_map["province"]["summary"] == "已对齐：山东"
    assert priority_compare_field_map["source_title"]["summary"] == "已对齐：山东来源 102"
    assert priority_compare_field_map["source_url"]["summary"] == "已对齐：source.example/102"
    assert quick_filter_map["all"]["count"] == 3
    assert quick_filter_map["high_priority"]["count"] == 1
    assert quick_filter_map["missing_chapter"]["count"] == 2
    assert quick_filter_map["duplicate_or_same_name"]["count"] == 2
    assert quick_filter_map["unresolved"]["count"] == 1

    focus_response = client.get(
        "/api/gaokao/review-summary",
        params={"focus": "missing_chapter", "sort": "updated_desc"},
    )
    assert focus_response.status_code == 200
    focus_payload = focus_response.json()

    assert focus_payload["active_focus"] == "missing_chapter"
    assert focus_payload["active_sort"] == "updated_desc"
    assert focus_payload["queue_total"] == 2
    assert [item["college_id"] for item in focus_payload["items"]] == [102, 103]
    assert focus_payload["duplicate_groups"][0]["item_count"] == 1
    assert focus_payload["priority_groups"][0]["key"] == "dup-urgent"
    assert any("缺章程" in item for item in focus_payload["highlights"])


def test_gaokao_college_options_support_live_search_and_fallback(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    name TEXT,
                    province TEXT,
                    review_status TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (id, college_code, name, province, review_status, updated_at)
                VALUES
                    (101, 'SD001', '山东示例大学', '山东', 'pending_manual_review', '2026-04-16 09:00:00'),
                    (102, 'HB001', '河北示例大学', '河北', 'unresolved', '2026-04-15 09:00:00')
                """
            )
        )

    live_response = client.get("/api/gaokao/college-options", params={"q": "山东示例", "limit": 5})
    assert live_response.status_code == 200
    live_payload = live_response.json()
    assert live_payload[0]["college_id"] == 101
    assert live_payload[0]["source_mode"] == "db_rc1_live"
    assert live_payload[0]["review_status"] == "pending_manual_review"


def test_gaokao_college_options_fallback_to_app_model(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.add_all(
            [
                College(name="山东后备大学", college_code="BK001", province="山东", is_active=True),
                College(name="河北后备大学", college_code="BK002", province="河北", is_active=True),
            ]
        )

    response = client.get("/api/gaokao/college-options", params={"q": "后备", "limit": 5})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]["source_mode"] == "app_model_fallback"


def test_gaokao_import_batches_filter_relevant_jobs(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.add_all(
            [
                ImportJob(job_type="student_import", source_filename="students.xlsx", status="success"),
                ImportJob(job_type="admission_import", source_filename="admissions.xlsx", status="success"),
                ImportJob(job_type="enrollment_plan_import", source_filename="plans.xlsx", status="processing"),
            ]
        )

    response = client.get("/api/gaokao/import-batches")
    assert response.status_code == 200
    payload = response.json()
    assert [item["source_filename"] for item in payload] == ["plans.xlsx", "admissions.xlsx"]


def test_gaokao_shandong_monitor_uses_current_models_as_fallback(client, app) -> None:
    with app.state.db.session_scope() as session:
        college = College(name="山东监控大学", college_code="37001", province="山东", is_active=True)
        major = Major(name="数据科学与大数据技术", major_code="080910T", is_active=True)
        session.add_all([college, major])
        session.flush()
        session.add(
            EnrollmentPlan(
                year=2026,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=major.id,
                major_group_code="A",
                major_name_snapshot="数据科学与大数据技术",
                major_code_snapshot="080910T",
                plan_count=12,
                subject_requirement="物理,化学",
                import_batch_name="sd-plan-batch-001",
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="本科批",
                college_id=college.id,
                major_id=major.id,
                student_type="general",
                min_score=602,
                min_rank=12000,
                is_active=True,
            )
        )
        session.add(
            ProvinceVolunteerRule(
                province="山东",
                year=2026,
                exam_mode="3+3",
                batch="本科批",
                candidate_type="general",
                volunteer_limit=96,
                volunteer_unit_type="院校专业组",
                is_active=True,
            )
        )
    response = client.get("/api/gaokao/shandong-monitor")
    assert response.status_code == 200
    payload = response.json()
    section_map = {item["key"]: item for item in payload["sections"]}

    assert payload["province"] == "山东"
    assert payload["ready_section_total"] == 5
    assert payload["gap_section_total"] == 1
    assert any("山东一分一段" in item for item in payload["priority_notes"])
    assert section_map["province_rules"]["record_total"] >= 1
    assert section_map["province_rules"]["status"] == "ready"
    assert section_map["score_transform_rules"]["record_total"] >= 1
    assert section_map["score_transform_rules"]["status"] == "ready"
    assert section_map["enrollment_plans"]["record_total"] >= 1
    assert section_map["enrollment_plans"]["latest_batch_label"] == "sd-plan-batch-001"
    assert section_map["subject_requirements"]["record_total"] >= 1
    assert section_map["subject_requirements"]["status"] == "ready"
    assert section_map["admission_results"]["record_total"] >= 1


def test_gaokao_services_support_current_raw_schema_and_province_aliases(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    college_name TEXT,
                    province TEXT,
                    official_site TEXT,
                    recruit_site TEXT,
                    chapter_url TEXT,
                    chapter_fallback_url TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college_chapter_rule (
                    id INTEGER PRIMARY KEY,
                    college_id INTEGER,
                    province TEXT,
                    year INTEGER,
                    chapter_url TEXT,
                    chapter_fallback_url TEXT,
                    review_status TEXT,
                    retrieval_status TEXT,
                    source_title TEXT,
                    source_url TEXT,
                    updated_at TEXT,
                    created_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE data_import_batch (
                    id INTEGER PRIMARY KEY,
                    batch_code TEXT,
                    domain TEXT,
                    data_type TEXT,
                    province TEXT,
                    target_year INTEGER,
                    source_name TEXT,
                    source_title TEXT,
                    version_label TEXT,
                    status TEXT,
                    total_records INTEGER,
                    started_at TEXT,
                    finished_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_province_rule (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    year INTEGER,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_score_transform_rule (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    year INTEGER,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE score_rank_segment (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    year INTEGER,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_subject_requirement (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_admission_result (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_admission_plan (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, college_name, province, official_site, recruit_site,
                    chapter_url, chapter_fallback_url, updated_at
                ) VALUES
                    (201, 'SD201', '山东真实库大学', 'sd', 'https://official.example/201', 'https://recruit.example/201',
                     'https://chapter.example/201', 'https://fallback.example/201', '2026-04-21 10:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college_chapter_rule (
                    id, college_id, province, year, chapter_url, chapter_fallback_url,
                    review_status, retrieval_status, source_title, source_url, updated_at, created_at
                ) VALUES
                    (1, 201, 'sd', 2025, 'https://chapter.example/201', 'https://fallback.example/201',
                     'pending_manual_review_with_official_candidate', 'official_fallback_candidate_available',
                     '招生章程查询', 'https://source.example/201', '2026-04-21 10:30:00', '2026-04-21 10:30:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO data_import_batch (
                    id, batch_code, domain, data_type, province, target_year,
                    source_name, source_title, version_label, status, total_records, started_at, finished_at
                ) VALUES
                    (1, 'IMP-001', 'gaokao', 'gaokao-admission-plan', 'sd', 2025,
                     'sd_staging', '2025年山东招生计划', 'DB RC1', 'completed', 6895,
                     '2026-04-21 09:00:00', '2026-04-21 09:30:00')
                """
            )
        )
        session.execute(text("INSERT INTO gaokao_province_rule (id, province, year, updated_at) VALUES (1, 'sd', 2025, '2026-04-21 09:31:00')"))
        session.execute(text("INSERT INTO gaokao_score_transform_rule (id, province, year, updated_at) VALUES (1, 'sd', 2025, '2026-04-21 09:32:00')"))
        session.execute(text("INSERT INTO score_rank_segment (id, province, year, updated_at) VALUES (1, 'sd', 2025, '2026-04-21 09:33:00')"))
        session.execute(text("INSERT INTO gaokao_subject_requirement (id, province, updated_at) VALUES (1, 'sd', '2026-04-21 09:34:00')"))
        session.execute(text("INSERT INTO gaokao_admission_result (id, province, updated_at) VALUES (1, 'sd', '2026-04-21 09:35:00')"))
        session.execute(text("INSERT INTO gaokao_admission_plan (id, province, updated_at) VALUES (1, 'sd', '2026-04-21 09:36:00')"))

    overview_response = client.get("/api/gaokao/data-overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["chapter_url_covered"] == 1
    assert overview_payload["fallback_url_covered"] == 1
    assert overview_payload["core_tables"][1]["key"] == "gaokao_college_chapter_rule"

    batches_response = client.get("/api/gaokao/import-batches")
    assert batches_response.status_code == 200
    batches_payload = batches_response.json()
    assert batches_payload[0]["source_type"] == "gaokao-admission-plan"
    assert batches_payload[0]["status"] == "success"
    assert batches_payload[0]["notes"] == ["山东 / 2025 / DB RC1"]

    shandong_response = client.get("/api/gaokao/shandong-monitor")
    assert shandong_response.status_code == 200
    shandong_payload = shandong_response.json()
    section_map = {item["key"]: item for item in shandong_payload["sections"]}
    assert shandong_payload["ready_section_total"] == 6
    assert section_map["province_rules"]["record_total"] == 1
    assert section_map["score_transform_rules"]["record_total"] == 1
    assert section_map["score_rank_segments"]["record_total"] == 1
    assert section_map["subject_requirements"]["record_total"] == 1
    assert section_map["admission_results"]["record_total"] == 1
    assert section_map["enrollment_plans"]["record_total"] == 1


def test_gaokao_review_and_evidence_support_chapter_rule_schema(client, app) -> None:
    with app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college (
                    id INTEGER PRIMARY KEY,
                    college_code TEXT,
                    college_name TEXT,
                    province TEXT,
                    official_site TEXT,
                    recruit_site TEXT,
                    chapter_url TEXT,
                    chapter_fallback_url TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                CREATE TABLE gaokao_college_chapter_rule (
                    id INTEGER PRIMARY KEY,
                    college_id INTEGER,
                    province TEXT,
                    year INTEGER,
                    chapter_url TEXT,
                    chapter_fallback_url TEXT,
                    review_status TEXT,
                    retrieval_status TEXT,
                    source_title TEXT,
                    source_url TEXT,
                    updated_at TEXT,
                    created_at TEXT
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college (
                    id, college_code, college_name, province, official_site, recruit_site,
                    chapter_url, chapter_fallback_url, updated_at
                ) VALUES
                    (301, 'SD301', '山东章程大学', 'sd', 'https://official.example/301', 'https://recruit.example/301',
                     NULL, 'https://fallback.example/301', '2026-04-21 10:00:00'),
                    (302, 'SD302', '山东待补大学', 'sd', NULL, NULL,
                     NULL, NULL, '2026-04-21 09:00:00')
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO gaokao_college_chapter_rule (
                    id, college_id, province, year, chapter_url, chapter_fallback_url,
                    review_status, retrieval_status, source_title, source_url, updated_at, created_at
                ) VALUES
                    (1, 301, 'sd', 2025, 'https://chapter.example/301', 'https://fallback.example/301',
                     'pending_manual_review_with_official_candidate', 'official_fallback_candidate_available',
                     '招生章程查询', 'https://source.example/301', '2026-04-21 10:30:00', '2026-04-21 10:30:00'),
                    (2, 302, 'sd', 2025, NULL, NULL,
                     'pending_manual_review', 'pending_official_lookup',
                     '招生章程查询', 'https://source.example/302', '2026-04-21 10:20:00', '2026-04-21 10:20:00')
                """
            )
        )

    review_response = client.get("/api/gaokao/review-summary", params={"keyword": "山东"})
    assert review_response.status_code == 200
    review_payload = review_response.json()
    assert review_payload["counts"][0]["count"] == 1
    assert review_payload["counts"][1]["count"] == 1
    item_map = {item["college_id"]: item for item in review_payload["items"]}
    assert item_map[301]["chapter_url"] == "https://chapter.example/301"
    assert item_map[301]["province"] == "山东"
    assert review_payload["items"][0]["college_id"] == 302
    assert review_payload["items"][0]["province"] == "山东"

    options_response = client.get("/api/gaokao/college-options", params={"q": "章程大学"})
    assert options_response.status_code == 200
    options_payload = options_response.json()
    assert options_payload[0]["review_status"] == "pending_manual_review_with_official_candidate"
    assert options_payload[0]["province"] == "山东"

    evidence_response = client.get("/api/gaokao/college-evidence/301")
    assert evidence_response.status_code == 200
    evidence_payload = evidence_response.json()
    assert evidence_payload["chapter_url"] == "https://chapter.example/301"
    assert evidence_payload["fallback_url"] == "https://fallback.example/301"
    assert evidence_payload["review_status"] == "pending_manual_review_with_official_candidate"
