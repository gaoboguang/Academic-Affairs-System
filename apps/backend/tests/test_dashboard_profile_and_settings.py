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


def test_dashboard_profiles_and_system_settings(client) -> None:
    exam_id = create_exam_with_scores(client)

    upload_response = client.post(
        "/api/files/upload",
        data={"category": "growth_archive"},
        files={"file": ("award.txt", b"award", "text/plain")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    growth_response = client.post(
        "/api/archives/students/1/records",
        json={
            "occurred_on": "2026-04-12",
            "record_type": "奖励记录",
            "title": "市级竞赛获奖",
            "content": "获得二等奖",
            "owner_name": "班主任",
            "note": "",
            "attachment_file_ids": [file_id],
            "is_active": True,
        },
    )
    assert growth_response.status_code == 200

    admission_response = client.post(
        "/api/admissions/import",
        files={
            "file": (
                "admissions.xlsx",
                build_admission_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert admission_response.status_code == 200

    recommendation_response = client.post(
        "/api/recommendations/generate",
        json={
            "student_id": 1,
            "exam_id": exam_id,
            "province": "广东",
            "student_rank_override": 25000,
        },
    )
    assert recommendation_response.status_code == 200

    dashboard_response = client.get("/api/dashboard/summary")
    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["recent_exam"]["exam_id"] == exam_id
    assert dashboard_payload["exam_total"] >= 1
    assert dashboard_payload["score_record_total"] >= 6
    assert "data_health" in dashboard_payload
    assert dashboard_payload["data_health"]["p0_gap_count"] >= 0
    issue_codes = {item["code"] for item in dashboard_payload["data_quality_issues"]}
    assert "student_open_history_missing" in issue_codes

    student_profile_response = client.get("/api/students/1/profile")
    assert student_profile_response.status_code == 200
    student_profile = student_profile_response.json()
    assert student_profile["performance_summary"]["latest_exam_id"] == exam_id
    assert len(student_profile["recent_growth_records"]) == 1
    assert len(student_profile["recommendation_history"]) == 1
    assert len(student_profile["attachments"]) == 1

    title_history_response = client.put(
        "/api/teachers/1/title-histories",
        json=[
            {
                "title_code": "level_2",
                "start_date": "2022-09-01",
                "end_date": "2024-08-31",
                "note": "年度晋升",
                "is_active": True,
            },
            {
                "title_code": "level_1",
                "start_date": "2024-09-01",
                "end_date": None,
                "note": "当前职称",
                "is_active": True,
            },
        ],
    )
    assert title_history_response.status_code == 200
    assert len(title_history_response.json()) == 2

    teacher_profile_response = client.get("/api/teachers/1/profile")
    assert teacher_profile_response.status_code == 200
    teacher_profile = teacher_profile_response.json()
    assert len(teacher_profile["title_histories"]) == 2
    assert teacher_profile["recent_exam_trends"][0]["exam_id"] == exam_id
    assert teacher_profile["peer_comparisons"][0]["teacher_id"] == 1

    config_groups_response = client.get("/api/system/config-groups")
    assert config_groups_response.status_code == 200
    config_group_codes = {item["config_group"] for item in config_groups_response.json()}
    assert {"analytics", "recommendation", "system"}.issubset(config_group_codes)

    repair_scan_response = client.get("/api/system/data-repair/scan")
    assert repair_scan_response.status_code == 200
    repair_issue_codes = {item["code"] for item in repair_scan_response.json()["issues"]}
    assert "student_open_history_missing" in repair_issue_codes

    repair_execute_response = client.post(
        "/api/system/data-repair/execute",
        json={"action_code": "repair_student_class_history"},
    )
    assert repair_execute_response.status_code == 200
    repair_payload = repair_execute_response.json()
    assert repair_payload["repaired_count"] == 3
    remaining_issue_codes = {item["code"] for item in repair_payload["scan"]["issues"]}
    assert "student_open_history_missing" not in remaining_issue_codes
