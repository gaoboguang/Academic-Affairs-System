from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import text


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
                    ('sd', 2025, 'summer_total', 'all', 650, 120, 10000, 10000),
                    ('sd', 2025, 'summer_total', 'all', 620, 180, 20000, 20000),
                    ('sd', 2025, 'summer_total', 'all', 590, 220, 30000, 30000),
                    ('sd', 2025, 'summer_total', 'all', 580, 280, 42000, 42000),
                    ('sd', 2025, 'summer_total', 'all', 0, 100, 700000, 700000)
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


def _build_score_workbook(exam_name: str, rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["考试名称", "学号", "姓名", "班级", "科目", "分数", "缺考标记", "备注"])
    for row in rows:
        sheet.append([exam_name, *row])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _create_exam_with_scores(client, *, name: str, exam_date: str, rows: list[list[object]]) -> int:
    exam_response = client.post(
        "/api/exams",
        json={
            "name": name,
            "exam_type": "月考",
            "exam_date": exam_date,
            "semester_id": 2,
            "grade_scope_json": [1],
            "is_trend_enabled": True,
            "status": "published",
            "note": "",
            "is_active": True,
        },
    )
    assert exam_response.status_code == 200
    exam_id = exam_response.json()["id"]
    subject_response = client.post(
        f"/api/exams/{exam_id}/subjects",
        json=[
            {
                "subject_id": 1,
                "full_score": 150,
                "is_in_total": True,
                "excellent_line": 110,
                "pass_line": 90,
                "sort_order": 1,
                "is_active": True,
            },
            {
                "subject_id": 2,
                "full_score": 150,
                "is_in_total": True,
                "excellent_line": 110,
                "pass_line": 90,
                "sort_order": 2,
                "is_active": True,
            },
        ],
    )
    assert subject_response.status_code == 200
    import_response = client.post(
        f"/api/exams/{exam_id}/scores/import",
        data={"strategy": "overwrite", "rebuild": "true"},
        files={
            "file": (
                "scores.xlsx",
                _build_score_workbook(name, rows),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_response.status_code == 200
    return exam_id


def test_manual_score_uses_previous_year_score_rank_segment(client) -> None:
    _create_score_rank_segment_table(client)

    response = client.post(
        "/api/recommendations/gaokao-score-projections/calculate",
        json={
            "student_id": 1,
            "target_year": 2026,
            "province": "山东",
            "source_mode": "manual_score",
            "manual_score": 620,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_rank"] == 20000
    assert payload["predicted_score"] == 620
    assert payload["confidence_level"] == "medium"
    assert payload["rank_projection_basis"] == "previous_year_score_rank_segment"
    assert payload["calculation_detail_json"]["score_rank_segment"]["used_year"] == 2025
    assert "2026 年一分一段暂缺" in payload["calculation_detail_json"]["notes"][0]


def test_manual_score_uses_general_summer_score_rank_filters(client) -> None:
    _create_mixed_score_rank_segment_table(client)

    response = client.post(
        "/api/recommendations/gaokao-score-projections/calculate",
        json={
            "student_id": 1,
            "target_year": 2026,
            "province": "山东",
            "source_mode": "manual_score",
            "manual_score": 620,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["predicted_rank"] == 20000
    assert payload["calculation_detail_json"]["score_rank_segment"]["used_score"] == 600


def test_manual_rank_projection_can_be_saved_and_listed(client) -> None:
    response = client.post(
        "/api/recommendations/gaokao-score-projections",
        json={
            "student_id": 1,
            "target_year": 2026,
            "province": "山东",
            "source_mode": "manual_rank",
            "manual_score": 615,
            "manual_rank": 18000,
            "note": "班主任手动确认",
        },
    )

    assert response.status_code == 200
    created = response.json()
    assert created["id"]
    assert created["predicted_rank"] == 18000
    assert created["rank_range_low"] == 18000
    assert created["rank_range_high"] == 18000
    assert created["confidence_level"] == "high"
    assert created["rank_projection_basis"] == "manual_rank"

    list_response = client.get("/api/recommendations/gaokao-score-projections?student_id=1&target_year=2026")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["note"] == "班主任手动确认"

    detail_response = client.get(f"/api/recommendations/gaokao-score-projections/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["student_name"] == "张三"


def test_exam_projection_combines_recent_scores_and_marks_school_estimate(client) -> None:
    _create_score_rank_segment_table(client)
    first_exam_id = _create_exam_with_scores(
        client,
        name="2026届高三一模",
        exam_date="2026-03-01",
        rows=[
            ["2026001", "张三", "1班", "语文", 112, "", ""],
            ["2026001", "张三", "1班", "数学", 120, "", ""],
            ["2026002", "李四", "1班", "语文", 105, "", ""],
            ["2026002", "李四", "1班", "数学", 110, "", ""],
            ["2026003", "王五", "2班", "语文", 96, "", ""],
            ["2026003", "王五", "2班", "数学", 100, "", ""],
        ],
    )
    second_exam_id = _create_exam_with_scores(
        client,
        name="2026届高三二模",
        exam_date="2026-04-01",
        rows=[
            ["2026001", "张三", "1班", "语文", 118, "", ""],
            ["2026001", "张三", "1班", "数学", 125, "", ""],
            ["2026002", "李四", "1班", "语文", 110, "", ""],
            ["2026002", "李四", "1班", "数学", 120, "", ""],
            ["2026003", "王五", "2班", "语文", 98, "", ""],
            ["2026003", "王五", "2班", "数学", 96, "", ""],
        ],
    )

    response = client.post(
        "/api/recommendations/gaokao-score-projections/calculate",
        json={
            "student_id": 1,
            "target_year": 2026,
            "province": "山东",
            "source_mode": "exam_projection",
            "selected_exam_ids": [first_exam_id, second_exam_id],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_mode"] == "exam_projection"
    assert payload["selected_exam_ids_json"] == [first_exam_id, second_exam_id]
    assert payload["predicted_score"] > 590
    assert payload["predicted_rank"] == 30000
    assert payload["rank_range_low"] < payload["predicted_rank"] < payload["rank_range_high"]
    assert payload["confidence_level"] == "medium"
    notes = payload["calculation_detail_json"]["notes"]
    assert any("校内估算" in item for item in notes)
    assert payload["calculation_detail_json"]["calibration_status"] == "missing_school_gaokao_calibration"


def test_manual_score_without_score_rank_segment_returns_clear_error(client) -> None:
    response = client.post(
        "/api/recommendations/gaokao-score-projections/calculate",
        json={
            "student_id": 1,
            "target_year": 2026,
            "province": "山东",
            "source_mode": "manual_score",
            "manual_score": 620,
        },
    )

    assert response.status_code == 400
    assert "缺少可用一分一段表" in response.json()["detail"]
