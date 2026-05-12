from __future__ import annotations

from sqlalchemy import text

from app.models import AdmissionRecord, College, EnrollmentPlan, Major, StudentPathwayProfile
from app.schemas.recommendation import VolunteerWorkbenchCandidateRead
from app.services._recommendations_workbench import _candidate_sort_key
from app.services._recommendations_volunteer_options import infer_art_track_from_text

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


def _seed_mixed_art_plans_with_history(app) -> None:
    with app.state.db.session_scope() as session:
        college = College(
            name="山东艺术类别过滤测试大学",
            college_code="SDART02",
            province="山东",
            city="济南",
            supports_art=True,
            is_active=True,
        )
        music_major = Major(
            name="音乐表演",
            major_code="130201",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        music_plan_major = Major(
            name="音乐表演（音乐类（音乐表演）统考成绩）",
            major_code="130201",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        design_major = Major(
            name="产品设计",
            major_code="130504",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        opera_major = Major(
            name="戏曲音乐",
            major_code="130315",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        ambiguous_art_major = Major(
            name="影视多媒体技术",
            major_code="560208",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        music_theater_major = Major(
            name="表演",
            major_code="130301",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        session.add_all([college, music_major, music_plan_major, design_major, opera_major, ambiguous_art_major, music_theater_major])
        session.flush()
        for year in (2023, 2024, 2025):
            session.add(
                EnrollmentPlan(
                    year=year,
                    province="山东",
                    batch="本科批",
                    exam_mode="3+3",
                    college_id=college.id,
                    major_id=music_plan_major.id,
                    college_code_snapshot="SDART02",
                    major_group_code="M01",
                    major_name_snapshot="音乐表演（音乐类（音乐表演）统考成绩）",
                    major_code_snapshot="130201",
                    plan_count=10 + year - 2023,
                    tuition_fee=f"{12000 + year - 2023} 元/年",
                    student_type="art",
                    source_note="音乐类招生计划",
                    is_active=True,
                )
            )
            session.add(
                AdmissionRecord(
                    year=year,
                    province="山东",
                    batch="艺术类本科批",
                    college_id=college.id,
                    major_id=music_major.id,
                    student_type="art",
                    art_track="音乐类" if year == 2025 else None,
                    min_score=480 + year - 2023,
                    min_rank=3000 - (year - 2023) * 100,
                    plan_count=8 + year - 2023,
                    source_note="音乐类录取样本",
                    is_active=True,
                )
            )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=design_major.id,
                college_code_snapshot="SDART02",
                major_group_code="D01",
                major_name_snapshot="产品设计（美术与设计类统考成绩）",
                major_code_snapshot="130504",
                plan_count=20,
                tuition_fee="13000 元/年",
                student_type="art",
                source_note="美术与设计类招生计划",
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=music_theater_major.id,
                college_code_snapshot="SDART02",
                major_group_code="T01",
                major_name_snapshot="表演（音乐剧）",
                major_code_snapshot="130301",
                plan_count=5,
                tuition_fee="14000 元/年",
                student_type="art",
                source_note="艺术类招生计划",
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=opera_major.id,
                college_code_snapshot="SDART02",
                major_group_code="O01",
                major_name_snapshot="戏曲音乐（戏曲类联考成绩）",
                major_code_snapshot="130315",
                plan_count=6,
                tuition_fee="9000 元/年",
                student_type="art",
                source_note="戏曲类招生计划",
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="本科批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=ambiguous_art_major.id,
                college_code_snapshot="SDART02",
                major_group_code="V01",
                major_name_snapshot="影视多媒体技术",
                major_code_snapshot="560208",
                plan_count=9,
                tuition_fee="11000 元/年",
                student_type="art",
                source_note="艺术类招生计划",
                is_active=True,
            )
        )


def _seed_music_history_without_plan(app) -> None:
    with app.state.db.session_scope() as session:
        college = College(
            name="山东历史音乐参考大学",
            college_code="HISTM01",
            province="山东",
            city="青岛",
            supports_art=True,
            is_active=True,
        )
        music_major = Major(
            name="音乐教育",
            major_code="130212",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        design_major = Major(
            name="视觉传达设计",
            major_code="130502",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        session.add_all([college, music_major, design_major])
        session.flush()
        for year, score, count in ((2025, 486, 18), (2024, 481, 16), (2023, 478, 15)):
            session.add(
                AdmissionRecord(
                    year=year,
                    province="山东",
                    batch="艺术类本科批",
                    college_id=college.id,
                    major_id=music_major.id,
                    student_type="art",
                    art_track="music",
                    min_score=score,
                    min_rank=None,
                    plan_count=count,
                    source_note="山东艺术类本科批音乐类投档历史；缺招生计划",
                    is_active=True,
                )
            )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="艺术类本科批",
                college_id=college.id,
                major_id=design_major.id,
                student_type="art",
                art_track="fine_art_design",
                min_score=492,
                plan_count=20,
                source_note="山东艺术类本科批美术与设计类投档历史",
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


def test_art_candidate_type_with_invalid_art_track_is_blocked(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_mixed_art_plans_with_history(app)

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
            "art_track": "art",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
            "professional_score": 240,
            "use_historical_mapping": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "blocked"
    assert payload["source_preview"]["candidate_count"] == 0
    assert any(item["code"] == "invalid_art_track" for item in payload["readiness"]["items"])


def test_art_track_short_chinese_label_normalizes_to_music(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_mixed_art_plans_with_history(app)

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
            "art_track": "音乐",
            "score_input_mode": "estimated_score",
            "culture_score": 370,
            "professional_score": 240,
            "use_historical_mapping": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["art_track"] == "music"
    assert payload["readiness"]["status"] in {"ready", "warning"}
    assert any("音乐类" in item and "标准口径" in item for item in payload["input_notes"])
    candidates = [
        item["candidate"]
        for group in payload["groups"].values()
        for item in group["candidates"]
    ]
    assert candidates
    assert all("设计" not in item["major_name"] for item in candidates)


def test_music_history_without_enrollment_plan_returns_history_only_candidate(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_music_history_without_plan(app)

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
    candidates = [
        item["candidate"]
        for group in payload["groups"].values()
        for item in group["candidates"]
    ]
    music_candidate = next(
        item
        for item in candidates
        if item["college_name"] == "山东历史音乐参考大学" and item["major_name"] == "音乐教育"
    )
    assert music_candidate["plan_id"] < 0
    assert music_candidate["reference_scope"] == "history_only"
    assert music_candidate["plan_count"] == 0
    assert "history_only_reference" in music_candidate["risk_flags_json"]
    assert "missing_enrollment_plan" in music_candidate["risk_flags_json"]
    assert any("缺招生计划，仅历史参考" in item for item in music_candidate["match_notes_json"])
    assert music_candidate["recent_history_json"] == [
        {
            "year": 2025,
            "batch": "艺术类本科批",
            "plan_count": None,
            "admission_count": 18,
            "min_score": 486.0,
            "min_rank": None,
            "tuition_fee": None,
        },
        {
            "year": 2024,
            "batch": "艺术类本科批",
            "plan_count": None,
            "admission_count": 16,
            "min_score": 481.0,
            "min_rank": None,
            "tuition_fee": None,
        },
        {
            "year": 2023,
            "batch": "艺术类本科批",
            "plan_count": None,
            "admission_count": 15,
            "min_score": 478.0,
            "min_rank": None,
            "tuition_fee": None,
        },
    ]
    assert all(item["major_name"] != "视觉传达设计" for item in candidates)


def test_candidate_sort_prioritizes_plan_candidates_over_history_only() -> None:
    plan_candidate = VolunteerWorkbenchCandidateRead(
        plan_id=100,
        year=2025,
        province="山东",
        batch="本科批",
        exam_mode="3+3",
        college_id=100,
        college_name="ZZZ音乐计划大学",
        major_id=100,
        major_name="音乐表演",
        plan_count=12,
        student_type="art",
        result_type="challenge",
        score_basis="score",
        reference_scope="major",
        reason_text="有招生计划和专业历史线。",
    )
    history_only_candidate = VolunteerWorkbenchCandidateRead(
        plan_id=-200,
        year=2026,
        province="山东",
        batch="艺术类本科批统考",
        exam_mode="3+3",
        college_id=200,
        college_name="AAA历史参考大学",
        major_id=200,
        major_name="音乐教育",
        plan_count=0,
        student_type="art",
        result_type="challenge",
        score_basis="score",
        reference_scope="history_only",
        reason_text="缺招生计划，仅历史参考。",
    )

    ordered = sorted(
        [history_only_candidate, plan_candidate],
        key=lambda item: _candidate_sort_key(item, {"艺术类本科批统考": 1}),
    )

    assert ordered[0].reference_scope == "major"


def test_art_track_infers_music_performance_direction_as_music() -> None:
    assert infer_art_track_from_text("音乐表演(小号)") == "music"
    assert infer_art_track_from_text("音乐表演(流行电吉他)") == "music"
    assert infer_art_track_from_text("戏曲音乐(京剧)") == "opera"


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


def test_music_art_track_filters_design_and_opera_plans_and_returns_recent_history(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_mixed_art_plans_with_history(app)

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
    candidates = [
        item["candidate"]
        for group in payload["groups"].values()
        for item in group["candidates"]
    ]
    assert candidates
    major_names = {item["major_name"] for item in candidates}
    assert "音乐表演（音乐类（音乐表演）统考成绩）" in major_names
    assert "表演（音乐剧）" in major_names
    assert "产品设计" not in major_names
    assert "戏曲音乐" not in major_names
    assert "影视多媒体技术" not in major_names
    music_candidate = next(item for item in candidates if item["major_name"] == "音乐表演（音乐类（音乐表演）统考成绩）")
    assert music_candidate["recent_history_json"] == [
        {
            "year": 2025,
            "batch": "本科批",
            "plan_count": 12,
            "admission_count": 10,
            "min_score": 482.0,
            "min_rank": 2800,
            "tuition_fee": "12002 元/年",
        },
        {
            "year": 2024,
            "batch": "本科批",
            "plan_count": 11,
            "admission_count": 9,
            "min_score": 481.0,
            "min_rank": 2900,
            "tuition_fee": "12001 元/年",
        },
        {
            "year": 2023,
            "batch": "本科批",
            "plan_count": 10,
            "admission_count": 8,
            "min_score": 480.0,
            "min_rank": 3000,
            "tuition_fee": "12000 元/年",
        },
    ]


def test_music_art_track_rejects_art_generic_design_plan_without_history(client, app) -> None:
    exam_id = create_exam_with_scores(client)
    _seed_mixed_art_plans_with_history(app)
    with app.state.db.session_scope() as session:
        college = College(
            name="山东交通学院截图复现",
            college_code="A466",
            province="山东",
            city="济南",
            supports_art=True,
            is_active=True,
        )
        design_major = Major(
            name="环境设计",
            major_code="130503",
            category="艺术学",
            is_art_related=True,
            is_active=True,
        )
        session.add_all([college, design_major])
        session.flush()
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="艺术类本科批统考",
                exam_mode="3+3",
                college_id=college.id,
                major_id=design_major.id,
                college_code_snapshot="A466",
                major_group_code="D02",
                major_name_snapshot="环境设计",
                major_code_snapshot="130503",
                plan_count=42,
                student_type="art",
                source_note="[gaokao-materialize]；candidate_type=艺术类；title=山东交通学院2025年山东省招生计划查询",
                import_batch_name="sd-2025-1",
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="艺术类本科批",
                college_id=college.id,
                major_id=design_major.id,
                student_type="art",
                art_track="美术与设计类",
                min_score=489,
                plan_count=42,
                source_note="类别：美术与设计类；录取最低分为综合分",
                is_active=True,
            )
        )

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
    candidates = [
        item["candidate"]
        for group in payload["groups"].values()
        for item in group["candidates"]
    ]
    names = {(item["college_name"], item["major_name"]) for item in candidates}
    assert ("山东交通学院截图复现", "环境设计") not in names
    assert all("设计" not in item["major_name"] for item in candidates)
