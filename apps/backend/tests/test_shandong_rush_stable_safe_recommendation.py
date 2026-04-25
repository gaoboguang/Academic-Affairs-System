from __future__ import annotations

from sqlalchemy import text

from app.services._recommendations_shandong_rush_stable_safe import _subject_requirement_satisfied


def _seed_candidate(
    client,
    *,
    college_name: str,
    major_name: str,
    ranks_by_year: dict[int, int],
    scores_by_year: dict[int, float] | None = None,
    plan_counts_by_year: dict[int, int] | None = None,
    subject_requirement: str | None = None,
    target_plan_count: int | None = 12,
    source_document_id: int = 9001,
) -> None:
    from app.models import AdmissionRecord, College, EnrollmentPlan, Major

    with client.app.state.db.session_scope() as session:
        college = College(
            name=college_name,
            college_code=f"B4C{source_document_id}",
            province="山东",
            city="济南",
            school_level_tags_json=["本科"],
            is_active=True,
        )
        major = Major(
            name=major_name,
            major_code=f"B4M{source_document_id}",
            is_active=True,
        )
        session.add_all([college, major])
        session.flush()
        for year, rank in ranks_by_year.items():
            session.add(
                AdmissionRecord(
                    year=year,
                    province="山东",
                    batch="常规批",
                    college_id=college.id,
                    major_id=major.id,
                    student_type="general",
                    art_track="",
                    subject_requirement=subject_requirement,
                    min_score=(scores_by_year or {}).get(year, 600.0),
                    min_rank=rank,
                    plan_count=(plan_counts_by_year or {}).get(year, 10),
                    source_note=f"{year} 山东普通类投档表",
                    source_document_id=source_document_id + year,
                    is_active=True,
                )
            )
        if target_plan_count is not None:
            session.add(
                EnrollmentPlan(
                    year=2026,
                    province="山东",
                    batch="常规批",
                    exam_mode="3+3",
                    college_id=college.id,
                    major_id=major.id,
                    college_code_snapshot=college.college_code,
                    major_group_code=f"B4G{source_document_id}",
                    major_name_snapshot=major.name,
                    major_code_snapshot=major.major_code,
                    plan_count=target_plan_count,
                    subject_requirement=subject_requirement,
                    student_type="general",
                    source_document_id=source_document_id + 2026,
                    is_active=True,
                )
            )


def _create_score_rank_segment_table(client) -> None:
    with client.app.state.db.session_scope() as session:
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
                )
                VALUES
                    ('sd', 2025, 'summer_total', 'all', 620, 100, 10000, 10000),
                    ('sd', 2025, 'summer_total', 'all', 600, 100, 20000, 20000)
                """
            )
        )


def _create_mixed_score_rank_segment_table(client) -> None:
    with client.app.state.db.session_scope() as session:
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
                )
                VALUES
                    ('sd', 2025, 'spring_total', 'all', 620, 1, 1, 1),
                    ('sd', 2025, 'summer_total', 'spring', 620, 2, 2, 2),
                    ('广东', 2025, 'summer_total', 'all', 620, 3, 3, 3),
                    ('sd', 2025, 'summer_total', 'all', 600, 100, 20000, 20000)
                """
            )
        )


def test_shandong_rush_stable_safe_preview_classifies_and_explains(client) -> None:
    _seed_candidate(
        client,
        college_name="B4保底测试大学",
        major_name="B4保底专业",
        ranks_by_year={2025: 15000, 2024: 16000, 2023: 15500},
        target_plan_count=15,
        source_document_id=9100,
    )
    _seed_candidate(
        client,
        college_name="B4稳妥测试大学",
        major_name="B4稳妥专业",
        ranks_by_year={2025: 11200, 2024: 11800, 2023: 12000},
        target_plan_count=9,
        source_document_id=9200,
    )
    _seed_candidate(
        client,
        college_name="B4冲刺测试大学",
        major_name="B4冲刺专业",
        ranks_by_year={2025: 9500, 2024: 9800, 2023: 9700},
        target_plan_count=8,
        source_document_id=9300,
    )
    _seed_candidate(
        client,
        college_name="B4数据不足测试大学",
        major_name="B4数据不足专业",
        ranks_by_year={2025: 18000},
        target_plan_count=6,
        source_document_id=9400,
    )
    _seed_candidate(
        client,
        college_name="B4计划缺失测试大学",
        major_name="B4计划缺失专业",
        ranks_by_year={2025: 13000, 2024: 13200, 2023: 13100},
        target_plan_count=None,
        source_document_id=9500,
    )
    _seed_candidate(
        client,
        college_name="B4选科不符测试大学",
        major_name="B4选科不符专业",
        ranks_by_year={2025: 17000, 2024: 17100, 2023: 17200},
        subject_requirement="物理",
        target_plan_count=5,
        source_document_id=9600,
    )

    response = client.post(
        "/api/recommendations/shandong-rush-stable-safe/preview",
        json={
            "student_id": 1,
            "source_mode": "manual_rank",
            "manual_rank": 10000,
            "manual_score": 620,
            "subject_combination": "历史 政治 地理",
            "major_keyword": "B4",
            "risk_preference": "balanced",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_rank"] == 10000
    assert payload["summary"]["excluded_subject_mismatch_count"] == 1

    safe_names = {item["major_name"] for item in payload["safe"]}
    stable_names = {item["major_name"] for item in payload["stable"]}
    rush_names = {item["major_name"] for item in payload["rush"]}
    watch_names = {item["major_name"] for item in payload["watch"]}

    assert "B4保底专业" in safe_names
    assert "B4稳妥专业" in stable_names
    assert "B4冲刺专业" in rush_names
    assert "B4数据不足专业" in watch_names
    assert "B4选科不符专业" not in safe_names | stable_names | rush_names | watch_names

    safe_candidate = next(item for item in payload["safe"] if item["major_name"] == "B4保底专业")
    assert safe_candidate["rank_margin"] > 0
    assert safe_candidate["rank_margin_ratio"] > 0.18
    assert safe_candidate["years_used"] == [2025, 2024, 2023]
    assert safe_candidate["historical_summary"]["weighted_reference_rank"]
    assert safe_candidate["source_document_ids"]
    assert "归为“保”" in safe_candidate["explanation_text"]

    incomplete_candidate = next(item for item in payload["watch"] if item["major_name"] == "B4数据不足专业")
    assert incomplete_candidate["data_confidence"] == "low"
    assert "three_year_data_incomplete" in incomplete_candidate["risk_flags"]
    assert "historical_data_missing" in incomplete_candidate["risk_flags"]

    plan_missing_candidate = next(item for item in payload["stable"] + payload["safe"] + payload["rush"] + payload["watch"] if item["major_name"] == "B4计划缺失专业")
    assert "plan_missing" in plan_missing_candidate["risk_flags"]


def test_shandong_rush_stable_safe_preview_uses_projection_snapshot(client) -> None:
    from app.models import StudentGaokaoScoreProjection

    _seed_candidate(
        client,
        college_name="B4快照测试大学",
        major_name="B4快照专业",
        ranks_by_year={2025: 12000, 2024: 12100, 2023: 12200},
        target_plan_count=10,
        source_document_id=9700,
    )
    with client.app.state.db.session_scope() as session:
        projection = StudentGaokaoScoreProjection(
            student_id=1,
            target_year=2026,
            province="山东",
            source_mode="exam_projection",
            predicted_score=618,
            predicted_rank=10000,
            rank_range_low=9000,
            rank_range_high=11500,
            confidence_level="medium",
            rank_projection_basis="school_exam_projection",
            selected_exam_ids_json=[1, 2],
            calculation_detail_json={"notes": ["校内估算，仅供参考"]},
            is_active=True,
        )
        session.add(projection)
        session.flush()
        projection_id = projection.id

    response = client.post(
        "/api/recommendations/shandong-rush-stable-safe/preview",
        json={
            "projection_id": projection_id,
            "source_mode": "projection",
            "major_keyword": "B4快照",
            "subject_combination": "历史 政治 地理",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_mode"] == "exam_projection"
    assert payload["rank_projection_basis"] == "school_exam_projection"
    assert any("校内估算" in item for item in payload["input_notes"])
    candidate = payload["stable"][0]
    assert "rank_projection_from_school_exam" in candidate["risk_flags"]
    assert "校内考试估算" in candidate["explanation_text"]


def test_shandong_rush_stable_safe_preview_manual_score_uses_previous_year_segment(client) -> None:
    _create_score_rank_segment_table(client)
    _seed_candidate(
        client,
        college_name="B4手动分测试大学",
        major_name="B4手动分专业",
        ranks_by_year={2025: 12000, 2024: 12100, 2023: 12200},
        target_plan_count=10,
        source_document_id=9800,
    )

    response = client.post(
        "/api/recommendations/shandong-rush-stable-safe/preview",
        json={
            "student_id": 1,
            "source_mode": "manual_score",
            "manual_score": 620,
            "major_keyword": "B4手动分",
            "subject_combination": "历史 政治 地理",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_rank"] == 10000
    assert payload["rank_projection_basis"] == "previous_year_score_rank_segment"
    candidate = payload["stable"][0]
    assert "rank_projection_from_previous_year" in candidate["risk_flags"]
    assert "上一年一分一段" in candidate["explanation_text"]


def test_shandong_manual_score_uses_shared_score_rank_filters(client) -> None:
    _create_mixed_score_rank_segment_table(client)
    _seed_candidate(
        client,
        college_name="B4过滤测试大学",
        major_name="B4过滤专业",
        ranks_by_year={2025: 24000, 2024: 24200, 2023: 24500},
        target_plan_count=10,
        source_document_id=9900,
    )

    response = client.post(
        "/api/recommendations/shandong-rush-stable-safe/preview",
        json={
            "student_id": 1,
            "source_mode": "manual_score",
            "manual_score": 620,
            "major_keyword": "B4过滤",
            "subject_combination": "历史 政治 地理",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_rank"] == 20000
    assert payload["rank_projection_basis"] == "previous_year_score_rank_segment"
    assert any("2025 年一分一段" in note for note in payload["input_notes"])


def test_subject_requirement_parser_handles_common_shandong_phrases() -> None:
    assert _subject_requirement_satisfied("不限", "历史 政治 地理")
    assert _subject_requirement_satisfied("不提科目要求", "历史 政治 地理")
    assert _subject_requirement_satisfied("物理", "物理 化学 生物")
    assert not _subject_requirement_satisfied("物理", "历史 政治 地理")
    assert _subject_requirement_satisfied("物理 化学", "物理 化学 生物")
    assert not _subject_requirement_satisfied("物理 化学", "物理 生物 地理")
    assert _subject_requirement_satisfied("物理或化学", "历史 化学 地理")
    assert not _subject_requirement_satisfied("物理或化学", "历史 政治 地理")
    assert _subject_requirement_satisfied("物理和化学均须选考", "物理 化学 生物")
    assert not _subject_requirement_satisfied("物理和化学均须选考", "物理 生物 地理")
