from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from test_exam_workflow import create_published_exam_with_scores


def _workbook_bytes(headers: list[str], rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _attendance_workbook(rows: list[list[object]]) -> bytes:
    return _workbook_bytes(["学号", "姓名", "日期", "范围", "节次", "状态", "原因", "备注"], rows)


def _behavior_workbook(rows: list[list[object]]) -> bytes:
    return _workbook_bytes(["学号", "姓名", "日期", "类型", "严重度", "标题", "说明", "处理人", "分值变化", "附件路径"], rows)


def test_attendance_behavior_import_dashboard_and_reports(client) -> None:
    exam_id, _payload = create_published_exam_with_scores(client)

    attendance_response = client.post(
        "/api/attendance/import",
        files={
            "file": (
                "attendance.xlsx",
                _attendance_workbook([
                    ["2026001", "张三", "2026-04-20", "日", "", "旷课", "未到校", ""],
                    ["2026002", "李四", "2026-04-20", "节次", "1", "迟到", "交通", ""],
                ]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert attendance_response.status_code == 200
    assert attendance_response.json()["created_rows"] == 2

    overwrite_response = client.post(
        "/api/attendance/import",
        files={
            "file": (
                "attendance-update.xlsx",
                _attendance_workbook([["2026001", "张三", "2026-04-20", "日", "", "病假", "医院证明", ""]]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert overwrite_response.status_code == 200
    assert overwrite_response.json()["updated_rows"] == 1

    truancy_response = client.post(
        "/api/attendance/import",
        files={
            "file": (
                "attendance-truancy.xlsx",
                _attendance_workbook([["2026001", "张三", "2026-04-21", "日", "", "旷课", "未到校", ""]]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert truancy_response.status_code == 200

    records_response = client.get("/api/attendance/records?student_id=1&start_date=2026-04-20&end_date=2026-04-20")
    assert records_response.status_code == 200
    assert records_response.json()["items"][0]["status"] == "病假"

    behavior_response = client.post(
        "/api/behavior/import",
        files={
            "file": (
                "behavior.xlsx",
                _behavior_workbook([
                    ["2026001", "张三", "2026-04-21", "安全事件", "严重", "离校未报备", "需当日核实", "李语文", "-5", ""],
                    ["2026001", "张三", "2026-04-21", "安全事件", "严重", "离校未报备", "重复行", "李语文", "-5", ""],
                ]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert behavior_response.status_code == 200
    behavior_payload = behavior_response.json()
    assert behavior_payload["success_rows"] == 1
    assert behavior_payload["skipped_rows"] == 1
    assert "重复行为" in " ".join(behavior_payload["notice_preview"])

    dashboard_response = client.get(
        f"/api/analytics/adviser-dashboard?class_id=1&exam_id={exam_id}&start_date=2026-04-20&end_date=2026-04-25"
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["overview"]["student_count"] == 2
    assert dashboard["overview"]["follow_up_count"] >= 1
    risk_by_name = {item["student_name"]: item for item in dashboard["risk_students"]}
    assert risk_by_name["张三"]["risk_level"] == "urgent"
    assert "旷课" in " ".join(risk_by_name["张三"]["reasons"])

    risk_response = client.get(
        f"/api/analytics/student-risk/1?exam_id={exam_id}&start_date=2026-04-20&end_date=2026-04-25"
    )
    assert risk_response.status_code == 200
    assert risk_response.json()["risk_level"] == "urgent"

    weekly_report_response = client.post(
        "/api/reports/export",
        json={
            "report_type": "adviser_weekly_summary",
            "class_id": 1,
            "exam_id": exam_id,
            "start_date": "2026-04-20",
            "end_date": "2026-04-25",
        },
    )
    assert weekly_report_response.status_code == 200
    assert weekly_report_response.json()["download_url"]

    followup_report_response = client.post(
        "/api/reports/export",
        json={
            "report_type": "student_followup_package",
            "student_id": 1,
            "exam_id": exam_id,
            "start_date": "2026-04-20",
            "end_date": "2026-04-25",
        },
    )
    assert followup_report_response.status_code == 200
    assert followup_report_response.json()["download_url"]


def test_attendance_and_behavior_import_validation(client) -> None:
    attendance_response = client.post(
        "/api/attendance/import",
        files={
            "file": (
                "bad-attendance.xlsx",
                _attendance_workbook([["2026999", "不存在", "2026-04-20", "日", "", "缺勤", "", ""]]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert attendance_response.status_code == 200
    payload = attendance_response.json()
    assert payload["failed_rows"] == 1
    assert "学号不存在" in payload["error_preview"][0]

    behavior_response = client.post(
        "/api/behavior/import",
        files={
            "file": (
                "bad-behavior.xlsx",
                _behavior_workbook([["2026001", "张三", "", "未知类型", "中", "测试", "", "", "", ""]]),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert behavior_response.status_code == 200
    assert behavior_response.json()["failed_rows"] == 1
    assert "日期不能为空" in behavior_response.json()["error_preview"][0]
