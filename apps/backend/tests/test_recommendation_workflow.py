from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


def build_score_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["考试名称", "学号", "姓名", "班级", "科目", "分数", "缺考标记", "备注"])
    sheet.append(["2026届高一4月月考", "2026001", "张三", "1班", "语文", "118", "", ""])
    sheet.append(["2026届高一4月月考", "2026001", "张三", "1班", "数学", "125", "", ""])
    sheet.append(["2026届高一4月月考", "2026002", "李四", "1班", "语文", "110", "", ""])
    sheet.append(["2026届高一4月月考", "2026002", "李四", "1班", "数学", "120", "", ""])
    sheet.append(["2026届高一4月月考", "2026003", "王五", "2班", "语文", "98", "", ""])
    sheet.append(["2026届高一4月月考", "2026003", "王五", "2班", "数学", "96", "", ""])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_admission_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["年份", "省份", "批次", "院校", "专业", "最低分", "最低位次", "学生类别", "数据来源说明"])
    sheet.append([2025, "广东", "本科批", "岭南科技大学", "软件工程", 585, 28000, "普通生", "近年数据"])
    sheet.append([2024, "广东", "本科批", "湾区信息大学", "计算机科学与技术", 568, 32000, "普通生", "近年数据"])
    sheet.append([2025, "广东", "本科批", "南方应用大学", "信息管理", 545, 40000, "普通生", "近年数据"])
    sheet.append([2025, "广东", "艺术本科", "岭南艺术学院", "视觉传达设计", 510, 26000, "美术", "艺体数据"])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def create_exam_with_scores(client) -> int:
    exam_response = client.post(
        "/api/exams",
        json={
            "name": "2026届高一4月月考",
            "exam_type": "月考",
            "exam_date": "2026-04-10",
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
                build_score_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_response.status_code == 200
    return exam_id


def test_admission_import_and_recommendation_generation(client) -> None:
    exam_id = create_exam_with_scores(client)

    import_response = client.post(
        "/api/admissions/import",
        files={
            "file": (
                "admissions.xlsx",
                build_admission_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_response.status_code == 200
    import_payload = import_response.json()
    assert import_payload["success_rows"] == 4
    assert import_payload["created_college_count"] == 4
    assert import_payload["created_major_count"] == 4

    admissions_response = client.get("/api/admissions?province=广东")
    assert admissions_response.status_code == 200
    assert len(admissions_response.json()) == 4

    general_response = client.post(
        "/api/recommendations/generate",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "student_rank_override": 31000,
        },
    )
    assert general_response.status_code == 200
    general_payload = general_response.json()
    assert general_payload["result_count"] == 3
    assert len(general_payload["challenge"]) == 1
    assert len(general_payload["steady"]) == 1
    assert len(general_payload["safe"]) == 1
    assert general_payload["challenge"][0]["college_name"] == "岭南科技大学"
    assert general_payload["steady"][0]["college_name"] == "湾区信息大学"
    assert general_payload["safe"][0]["college_name"] == "南方应用大学"

    settings_response = client.put(
        "/api/recommendations/settings",
        json={
            "safe_ratio_max": 0.85,
            "steady_ratio_max": 1.0,
            "rush_ratio_max": 1.15,
            "whitelist_college_ids": [],
            "blacklist_college_ids": [general_payload["challenge"][0]["college_id"]],
        },
    )
    assert settings_response.status_code == 200
    settings_payload = settings_response.json()
    assert settings_payload["blacklist_college_ids"] == [general_payload["challenge"][0]["college_id"]]
    assert settings_payload["strategy_presets"] == []

    preset_response = client.post(
        "/api/recommendations/strategy-presets",
        json={
            "name": "保守模板",
            "note": "优先稳保",
            "safe_ratio_max": 0.8,
            "steady_ratio_max": 0.95,
            "rush_ratio_max": 1.05,
            "whitelist_college_ids": [general_payload["safe"][0]["college_id"]],
            "blacklist_college_ids": [general_payload["challenge"][0]["college_id"]],
        },
    )
    assert preset_response.status_code == 200
    preset_payload = preset_response.json()
    assert len(preset_payload["strategy_presets"]) == 1
    assert preset_payload["strategy_presets"][0]["name"] == "保守模板"

    delete_preset_response = client.delete(
        f"/api/recommendations/strategy-presets/{preset_payload['strategy_presets'][0]['id']}"
    )
    assert delete_preset_response.status_code == 200
    assert delete_preset_response.json()["strategy_presets"] == []

    filtered_response = client.post(
        "/api/recommendations/generate",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "student_rank_override": 31000,
            "name": "黑名单过滤后",
        },
    )
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    filtered_colleges = {
        item["college_name"] for key in ("challenge", "steady", "safe") for item in filtered_payload[key]
    }
    assert "岭南科技大学" not in filtered_colleges

    art_response = client.post(
        "/api/recommendations/generate",
        json={
            "student_id": 3,
            "exam_id": exam_id,
            "province": "广东",
            "student_rank_override": 25000,
            "comprehensive_score": 540,
        },
    )
    assert art_response.status_code == 200
    art_payload = art_response.json()
    assert art_payload["result_count"] == 1
    assert art_payload["steady"][0]["college_name"] == "岭南艺术学院"
    assert "art_recommendation" in (art_payload["steady"][0]["risk_flags_json"] or [])

    history_response = client.get("/api/recommendations/history?student_id=1")
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert len(history_payload) == 2
    assert history_payload[0]["scheme_name"] == "黑名单过滤后"
    assert history_payload[0]["result_count"] == 2
    assert history_payload[1]["result_count"] == 3

    result_list_response = client.get(
        f"/api/recommendations/history/{general_payload['scheme_id']}/results?student_id=1"
    )
    assert result_list_response.status_code == 200
    assert len(result_list_response.json()) == 3
