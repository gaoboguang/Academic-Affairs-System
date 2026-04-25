from __future__ import annotations


def _first_student_id(client) -> int:
    response = client.get("/api/students", params={"page_size": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["items"]
    return data["items"][0]["id"]


def _pathway_by_code(items: list[dict], code: str) -> dict:
    return next(item for item in items if item["pathway_code"] == code)


def _evaluation_by_code(items: list[dict], code: str) -> dict:
    return next(item for item in items if item["pathway_code"] == code)


def test_bootstrap_shandong_pathways_creates_core_paths(client):
    response = client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] >= 10
    assert payload["created_count"] >= 10
    assert payload["rule_created_count"] >= 35

    list_response = client.get("/api/gaokao/pathways", params={"province": "山东"})
    assert list_response.status_code == 200
    pathways = list_response.json()
    codes = {item["pathway_code"] for item in pathways}
    assert {
        "summer_general_regular",
        "summer_general_early_a",
        "summer_special_type",
        "spring_exam_undergrad",
        "vocational_single_exam",
        "vocational_comprehensive",
        "art_undergrad",
        "sports_regular",
        "sports_single_exam",
        "high_level_sports",
    }.issubset(codes)

    general_pathway = _pathway_by_code(pathways, "summer_general_regular")
    assert general_pathway["source_document_id"]
    rule_response = client.get(f"/api/gaokao/pathways/{general_pathway['id']}/rules")
    assert rule_response.status_code == 200
    rules = rule_response.json()
    rule_codes = {item["rule_code"] for item in rules}
    assert {
        "d2_general_gaokao_registration",
        "d2_general_subject_combination",
        "d2_general_2026_plan_pending",
        "d2_general_chapter_review",
    }.issubset(rule_codes)
    assert all(item["source_document_id"] for item in rules if item["rule_code"].startswith("d2_"))

    single_pathway = _pathway_by_code(pathways, "vocational_single_exam")
    single_rules = client.get(f"/api/gaokao/pathways/{single_pathway['id']}/rules").json()
    assert {item["rule_code"] for item in single_rules}.issuperset(
        {"d2_single_registration", "d2_single_candidate_scope", "d2_single_school_chapter"}
    )
    assert any(item["manual_review_required"] for item in single_rules if item["rule_code"].startswith("d2_"))

    second_response = client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    assert second_response.status_code == 200
    assert second_response.json()["created_count"] == 0
    assert second_response.json()["rule_created_count"] == 0


def test_student_pathway_rule_engine_reports_passed_failed_and_unknown(client):
    client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    student_id = _first_student_id(client)
    pathways = client.get("/api/gaokao/pathways", params={"province": "山东"}).json()
    general_pathway = _pathway_by_code(pathways, "summer_general_regular")

    rule_response = client.post(
        f"/api/gaokao/pathways/{general_pathway['id']}/rules",
        json={
            "rule_code": "d1_test_gaokao_registration",
            "rule_name": "高考报名确认材料",
            "rule_type": "material_required",
            "severity": "required",
            "condition_json": {"type": "material_present", "key": "gaokao_registration"},
            "message_template": "补充高考报名确认材料后再评估。",
            "valid_from_year": 2026,
        },
    )
    assert rule_response.status_code == 200

    profile_response = client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "general",
            "subject_combination": "物理,化学,生物",
            "has_gaokao_registration": True,
            "materials_json": {},
        },
    )
    assert profile_response.status_code == 200

    preview_response = client.post(
        f"/api/gaokao/students/{student_id}/pathway-evaluations/preview",
        params={"target_year": 2026, "province": "山东"},
    )
    assert preview_response.status_code == 200
    general_eval = _evaluation_by_code(preview_response.json()["evaluations"], "summer_general_regular")
    assert general_eval["status"] == "insufficient_data"
    assert general_eval["matched_rules_json"][0]["result"] == "passed"
    assert general_eval["missing_materials_json"][0]["material_key"] == "gaokao_registration"
    assert general_eval["warning_rules_json"][0]["result"] == "unknown"

    client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "general",
            "subject_combination": "物理,化学,生物",
            "has_gaokao_registration": True,
            "materials_json": {"gaokao_registration": True},
        },
    )
    passed_preview = client.post(
        f"/api/gaokao/students/{student_id}/pathway-evaluations/preview",
        params={"target_year": 2026, "province": "山东"},
    )
    passed_eval = _evaluation_by_code(passed_preview.json()["evaluations"], "summer_general_regular")
    assert passed_eval["status"] == "possible"
    assert {item["result"] for item in passed_eval["matched_rules_json"]} == {"passed"}
    assert {item["rule_code"] for item in passed_eval["warning_rules_json"]}.issuperset(
        {"d2_general_2026_plan_pending", "d2_general_chapter_review"}
    )

    client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "spring_exam",
            "subject_combination": "物理,化学,生物",
            "has_gaokao_registration": True,
            "materials_json": {"gaokao_registration": True},
        },
    )
    failed_preview = client.post(
        f"/api/gaokao/students/{student_id}/pathway-evaluations/preview",
        params={"target_year": 2026, "province": "山东"},
    )
    failed_eval = _evaluation_by_code(failed_preview.json()["evaluations"], "summer_general_regular")
    assert failed_eval["status"] == "not_recommended"
    assert failed_eval["failed_rules_json"][0]["result"] == "failed"


def test_student_pathway_profile_missing_fields_are_readable(client):
    client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    student_id = _first_student_id(client)
    profile_response = client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "general",
            "materials_json": {},
        },
    )
    assert profile_response.status_code == 200

    preview_response = client.post(
        f"/api/gaokao/students/{student_id}/pathway-evaluations/preview",
        params={"target_year": 2026, "province": "山东"},
    )
    assert preview_response.status_code == 200
    general_eval = _evaluation_by_code(preview_response.json()["evaluations"], "summer_general_regular")
    missing_items = general_eval["missing_materials_json"]
    missing_by_key = {item["material_key"]: item for item in missing_items}
    assert missing_by_key["has_gaokao_registration"]["material_label"] == "高考报名状态"
    assert missing_by_key["subject_combination"]["material_label"] == "选科组合"
    assert missing_by_key["subject_combination"]["gap_type"] == "profile_field"
    assert "补充选科组合" in missing_by_key["subject_combination"]["next_action"]


def test_student_pathway_evaluations_can_be_persisted(client):
    client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    student_id = _first_student_id(client)
    client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "general",
            "materials_json": {},
        },
    )

    response = client.post(
        f"/api/gaokao/students/{student_id}/pathway-evaluations",
        params={"target_year": 2026, "province": "山东"},
    )
    assert response.status_code == 200
    evaluations = response.json()["evaluations"]
    assert evaluations
    assert all(item["id"] for item in evaluations)
