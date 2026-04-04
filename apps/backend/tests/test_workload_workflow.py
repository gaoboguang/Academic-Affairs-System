from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


def build_timetable_workbook(*rows: list[object]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["学期", "星期", "节次", "教师", "班级", "学科", "课程类型", "周次规则", "备注"])
    for row in rows:
        sheet.append(list(row))
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_timetable_import_and_manual_fix(client) -> None:
    content = build_timetable_workbook(
        ["2025-2026 下学期", 1, 1, "李语文", "1班", "语文", "正课", "全周", ""],
        ["2025-2026 下学期", 2, 2, "未知教师", "1班", "数学", "正课", "单周", "待修正"],
    )

    response = client.post(
        "/api/timetable/import",
        data={"semester_id": "2", "remark": "测试导入"},
        files={
            "file": (
                "timetable.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success_rows"] == 2
    assert payload["unresolved_rows"] == 1

    batches_response = client.get("/api/timetable/batches?semester_id=2")
    assert batches_response.status_code == 200
    batch_payload = batches_response.json()[0]
    assert batch_payload["entry_count"] == 2
    assert batch_payload["unresolved_count"] == 1

    entries_response = client.get(f"/api/timetable/batches/{payload['batch_id']}/entries?unresolved_only=true")
    assert entries_response.status_code == 200
    entries = entries_response.json()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["mapping_status"] == "unresolved"
    assert entry["raw_teacher_name"] == "未知教师"

    update_response = client.put(
        f"/api/timetable/entries/{entry['id']}",
        json={
            "teacher_id": 2,
            "class_id": 1,
            "subject_id": 2,
            "course_type": "regular",
            "note": "人工修正",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["mapping_status"] == "matched"
    assert updated["teacher_name"] == "王数学"
    assert updated["class_name"] == "1班"
    assert updated["subject_name"] == "数学"
    assert updated["course_type"] == "regular"


def test_workload_calculation_and_export(client) -> None:
    content = build_timetable_workbook(
        ["2025-2026 下学期", 1, 1, "李语文", "1班", "语文", "正课", "全周", ""],
        ["2025-2026 下学期", 2, 2, "王数学", "1班", "数学", "正课", "全周", ""],
        ["2025-2026 下学期", 3, 1, "李语文", "1班", "语文", "早读", "单周", ""],
    )
    import_response = client.post(
        "/api/timetable/import",
        data={"semester_id": "2", "remark": "计算测试"},
        files={
            "file": (
                "timetable_for_workload.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_response.status_code == 200
    batch_id = import_response.json()["batch_id"]

    rules_response = client.get("/api/workload/rules")
    assert rules_response.status_code == 200
    rule_versions = rules_response.json()
    assert len(rule_versions) >= 1
    default_rule = next(item for item in rule_versions if item["is_default"])

    extra_response = client.post(
        "/api/workload/extras",
        json={
            "teacher_id": 1,
            "semester_id": 2,
            "item_name": "备课组长",
            "quantity": 2,
            "coefficient": 1.5,
            "amount": None,
            "note": "测试额外量化",
        },
    )
    assert extra_response.status_code == 200
    assert extra_response.json()["teacher_name"] == "李语文"

    calculate_response = client.post(
        "/api/workload/calculate",
        json={
            "semester_id": 2,
            "rule_version_id": default_rule["id"],
            "batch_id": batch_id,
        },
    )
    assert calculate_response.status_code == 200
    assert calculate_response.json()["result_count"] == 2

    results_response = client.get(
        f"/api/workload/results?semester_id=2&rule_version_id={default_rule['id']}"
    )
    assert results_response.status_code == 200
    results = results_response.json()
    assert len(results) == 2

    teacher_one = next(item for item in results if item["teacher_id"] == 1)
    teacher_two = next(item for item in results if item["teacher_id"] == 2)
    assert teacher_one["weekly_hours"] == 1.5
    assert teacher_one["semester_hours"] == 30.0
    assert teacher_one["snapshot_json"]["head_teacher_bonus"] == 3.0
    assert teacher_one["semester_workload"] == 33.72
    assert teacher_two["weekly_hours"] == 1.0
    assert teacher_two["semester_workload"] == 21.78

    locked_rule_response = client.post(
        f"/api/workload/rules/{default_rule['id']}/items",
        json=[
            {
                "dimension_type": "subject",
                "match_key": "chinese",
                "coefficient": 1.2,
                "fixed_value": None,
                "note": "不允许直接修改已有结果规则",
                "is_active": True,
            }
        ],
    )
    assert locked_rule_response.status_code == 400
    assert "已有计算结果" in locked_rule_response.json()["detail"]

    export_response = client.get(
        f"/api/workload/results/export?semester_id=2&rule_version_id={default_rule['id']}"
    )
    assert export_response.status_code == 200
    assert "teacher_workload_export" in export_response.headers["content-disposition"]
