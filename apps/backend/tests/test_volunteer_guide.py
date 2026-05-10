from __future__ import annotations

from app.models import Student

from tests.test_recommendation_workflow import (
    build_admission_workbook,
    build_enrollment_plan_workbook,
    create_exam_with_scores,
)


def _prepare_basic_volunteer_data(client) -> int:
    exam_id = create_exam_with_scores(client)
    admission_import_response = client.post(
        "/api/admissions/import",
        files={
            "file": (
                "admissions.xlsx",
                build_admission_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert admission_import_response.status_code == 200
    plan_import_response = client.post(
        "/api/enrollment-plans/import",
        files={
            "file": (
                "enrollment-plans.xlsx",
                build_enrollment_plan_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert plan_import_response.status_code == 200
    rule_response = client.post(
        "/api/province-volunteer-rules",
        json={
            "province": "广东",
            "year": 2026,
            "exam_mode": "物理类",
            "batch": "本科批",
            "candidate_type": "general",
            "batch_order": 1,
            "total_score": 750,
            "volunteer_limit": 45,
            "volunteer_unit_type": "院校专业组",
            "subject_requirement_mode": "first_choice_reselect",
            "required_subjects_json": [],
            "first_choice_subjects_json": ["物理", "历史"],
            "reselect_subjects_json": ["化学", "生物", "政治", "地理"],
            "score_rule_summary": "再选科目按等级赋分",
            "parallel_rule_mode": "group_parallel",
            "max_major_per_unit": 6,
            "is_parallel": True,
            "allow_adjustment": True,
            "support_collect_round": True,
            "special_rules_json": ["需核对选科要求"],
            "note": "测试规则",
            "is_active": True,
        },
    )
    assert rule_response.status_code == 200
    return exam_id


def test_volunteer_guide_preview_groups_candidates_and_explains_evidence(client) -> None:
    exam_id = _prepare_basic_volunteer_data(client)

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
            "score_input_mode": "actual_rank",
            "student_rank_override": 31000,
            "subject_combination": "物理+化学",
            "target_regions_json": ["广东"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "ready"
    assert payload["readiness"]["blocking_count"] == 0
    assert payload["source_preview"]["candidate_count"] == 2
    assert payload["student_type"] == "general"
    assert payload["candidate_type"] == "general"
    assert payload["score_input_mode"] == "actual_rank"
    assert payload["applicable_rule_count"] == 1
    assert payload["applicable_rules"][0]["volunteer_limit"] == 45
    assert payload["input_notes"]
    assert sum(payload["groups"][key]["count"] for key in ("challenge", "steady", "safe")) == 2
    grouped_candidates = [
        item
        for key in ("challenge", "steady", "safe")
        for item in payload["groups"][key]["candidates"]
    ]
    first_candidate = next(item for item in grouped_candidates if item["evidence"]["strength"] == "major_history")
    assert first_candidate["candidate"]["college_name"] == "岭南科技大学"
    assert first_candidate["evidence"]["strength"] == "major_history"
    assert first_candidate["evidence"]["strength_label"] == "专业历史线"
    assert "专业线参考" in first_candidate["evidence"]["summary"]
    assert any(item["code"] == "add_to_draft" for item in payload["next_actions"])


def test_volunteer_guide_preview_reports_missing_readiness_without_crashing(client) -> None:
    exam_id = create_exam_with_scores(client)

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "target_year": 2025,
            "batch": "本科批",
            "exam_mode": "物理类",
            "candidate_type": "general",
            "score_input_mode": "actual_rank",
            "student_rank_override": 31000,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "blocked"
    assert any(item["code"] == "missing_rule_year" for item in payload["readiness"]["items"])
    assert any(item["code"] == "no_candidates" for item in payload["next_actions"])
    assert payload["groups"]["challenge"]["count"] == 0
    assert payload["groups"]["steady"]["count"] == 0
    assert payload["groups"]["safe"]["count"] == 0


def test_volunteer_guide_preview_keeps_special_type_as_initial_screening(client, app) -> None:
    exam_id = _prepare_basic_volunteer_data(client)
    with app.state.db.session_scope() as session:
        student = session.get(Student, 1)
        assert student is not None
        student.student_type = "comprehensive_evaluation"

    response = client.post(
        "/api/recommendations/volunteer-guide/preview",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "target_year": 2026,
            "batch": "本科批",
            "exam_mode": "物理类",
            "candidate_type": "comprehensive_evaluation",
            "score_input_mode": "actual_rank",
            "student_rank_override": 31000,
            "subject_combination": "物理+化学",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["readiness"]["status"] == "blocked"
    assert any(item["code"] == "special_type_initial_screening" for item in payload["readiness"]["items"])
    assert any(item["code"] == "manual_review_required" for item in payload["next_actions"])
