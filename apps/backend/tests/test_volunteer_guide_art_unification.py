from __future__ import annotations

from sqlalchemy import text

from app.models import College, EnrollmentPlan, Major, StudentPathwayProfile

from tests.test_recommendation_workflow import create_exam_with_scores


def _create_score_rank_segment_table(client) -> None:
    with client.app.state.db.session_scope() as session:
        session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS score_rank_segment (
                    id INTEGER PRIMARY KEY,
                    province TEXT,
                    year INTEGER,
                    score_type TEXT,
                    subject_group TEXT,
                    score NUMERIC,
                    segment_count INTEGER,
                    cumulative_count INTEGER,
                    rank_value INTEGER
                )
                """
            )
        )
        session.execute(
            text(
                """
                INSERT INTO score_rank_segment (
                    province, year, score_type, subject_group, score, segment_count, cumulative_count, rank_value
                ) VALUES
                    ('山东', 2025, 'summer_total', 'all', 582, 50, 12000, 12000),
                    ('山东', 2025, 'summer_total', 'all', 370, 80, 88000, 88000)
                """
            )
        )


def _seed_art_plan(app, *, year: int = 2026) -> None:
    with app.state.db.session_scope() as session:
        college = College(
            name="山东音乐统考测试大学",
            college_code="SDART01",
            province="山东",
            city="济南",
            supports_art=True,
            is_active=True,
        )
        major = Major(
            name="音乐表演统考测试专业",
            major_code="130201",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        session.add_all([college, major])
        session.flush()
        session.add(
            EnrollmentPlan(
                year=year,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=major.id,
                college_code_snapshot="SDART01",
                major_group_code="A01",
                major_name_snapshot=major.name,
                major_code_snapshot="130201",
                plan_count=12,
                student_type="art",
                source_note="艺术类本科批统考测试计划",
                import_batch_name="sd-art-alias-test",
                is_active=True,
            )
        )


def test_missing_target_year_plan_uses_historical_plan_when_mapping_enabled(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_art_plan(app, year=2025)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "山东",
            "target_year": 2026,
            "batch": "艺术类本科批统考",
            "exam_mode": "3+3",
            "candidate_type": "art",
            "art_track": "music",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
            "professional_score": 240,
            "use_historical_mapping": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_preview"]["candidate_count"] == 1
    candidate = payload["groups"]["challenge"]["candidates"][0]["candidate"]
    assert candidate["year"] == 2025
    assert "historical_plan_simulation" in candidate["risk_flags_json"]
    assert any("按 2025 年历史招生计划模拟" in item for item in candidate["match_notes_json"])
    assert any("2026 年正式招生计划" in item for item in payload["input_notes"])


def test_missing_target_year_plan_reports_clear_reason_without_historical_mapping(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_art_plan(app, year=2025)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "山东",
            "target_year": 2026,
            "batch": "艺术类本科批统考",
            "exam_mode": "3+3",
            "candidate_type": "art",
            "art_track": "music",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
            "professional_score": 240,
            "use_historical_mapping": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_preview"]["candidate_count"] == 0
    assert payload["readiness"]["status"] == "blocked"
    assert any(item["code"] == "missing_target_year_enrollment_plan" for item in payload["readiness"]["items"])
    assert any("2026 年正式招生计划尚未导入" in item["detail"] for item in payload["readiness"]["items"])


def test_volunteer_guide_options_expose_backend_canonical_fields(client) -> None:
    response = client.get("/api/recommendations/volunteer-guide/options?province=山东&year=2026")

    assert response.status_code == 200
    payload = response.json()
    candidate_values = {item["value"] for item in payload["candidate_types"]}
    art_values = {item["value"] for item in payload["art_tracks"]}
    batch_values = {item["value"] for item in payload["batches"]}
    score_mode_labels = {item["value"]: item["label"] for item in payload["score_input_modes"]}

    assert "art" in candidate_values
    assert "music" not in candidate_values
    assert "music" in art_values
    assert "艺术类本科批统考" in batch_values
    assert payload["batch_aliases"]["艺术本科批"] == "艺术类本科批统考"
    assert score_mode_labels["estimated_score_and_rank"] == "预估分 + 预估位次（本次考试/模拟推荐）"
    music_formula = payload["art_score_formulas"]["music"]
    assert music_formula["culture_weight"] == 0.5
    assert music_formula["professional_weight"] == 0.5


def test_art_batch_alias_and_legacy_candidate_type_normalize_for_preview(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_art_plan(app)

    with app.state.db.session_scope() as session:
        student = session.get(StudentPathwayProfile, 1)
        assert student is None
        profile = StudentPathwayProfile(
            student_id=1,
            province="山东",
            candidate_type="art",
            art_track="music",
            art_professional_score=240,
            art_professional_full_score=300,
            art_score_source="山东音乐类统考",
            is_active=True,
        )
        session.add(profile)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "山东",
            "target_year": 2026,
            "batch": "艺术本科批",
            "exam_mode": "3+3",
            "candidate_type": "music",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
            "subject_combination": "历史 政治 地理",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_type"] == "art"
    assert payload["art_track"] == "music"
    assert payload["normalized_batch"] == "艺术类本科批统考"
    assert payload["source_preview"]["total_score"] == 485
    assert payload["readiness"]["status"] in {"ready", "warning"}
    assert payload["applicable_rule_count"] >= 1
    assert sum(payload["groups"][key]["count"] for key in ("challenge", "steady", "safe", "watch")) >= 1
    assert any("艺术本科批" in item for item in payload["input_notes"])


def test_art_candidate_type_can_come_from_pathway_profile(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_art_plan(app)

    with app.state.db.session_scope() as session:
        profile = StudentPathwayProfile(
            student_id=1,
            province="山东",
            candidate_type="art",
            art_track="music",
            art_professional_score=240,
            art_professional_full_score=300,
            art_score_source="山东音乐类统考",
            is_active=True,
        )
        session.add(profile)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "山东",
            "target_year": 2026,
            "batch": "艺术本科批",
            "exam_mode": "3+3",
            "candidate_type": "",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["candidate_type"] == "art"
    assert payload["art_track"] == "music"
    assert payload["source_preview"]["professional_score"] == 240
    assert payload["source_preview"]["art_comprehensive_score"] == 485
    assert payload["readiness"]["status"] in {"ready", "warning"}


def test_art_preview_blocks_when_professional_score_missing(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_art_plan(app)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "山东",
            "target_year": 2026,
            "batch": "艺术类本科批统考",
            "exam_mode": "3+3",
            "candidate_type": "art",
            "art_track": "music",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "blocked"
    assert any(item["code"] == "missing_art_professional_score" for item in payload["readiness"]["items"])
    assert payload["source_preview"]["candidate_count"] == 0


def test_general_estimated_score_uses_score_rank_segment_not_school_rank(client) -> None:
    exam_id = create_exam_with_scores(client)
    _create_score_rank_segment_table(client)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "target_year": 2026,
            "batch": "本科批",
            "exam_mode": "物理类",
            "candidate_type": "general",
            "score_input_mode": "estimated_score",
            "comprehensive_score": 582,
            "student_rank_override": 58,
            "subject_combination": "物理 化学 生物",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_preview"]["effective_rank"] != 58
    assert any("一分一段" in item for item in payload["input_notes"])
    assert any("校内名次不用于志愿推荐" in item for item in payload["input_notes"])
