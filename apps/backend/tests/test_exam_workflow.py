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
    sheet.append(["2026届高一4月月考", "2026003", "王五", "2班", "数学", "", "缺考", ""])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_exam_score_import_and_analytics(client) -> None:
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
    assert len(subject_response.json()) == 2

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
    import_payload = import_response.json()
    assert import_payload["success_rows"] == 6
    assert import_payload["failed_rows"] == 0

    student_analytics = client.get(f"/api/analytics/students/1?exam_id={exam_id}")
    assert student_analytics.status_code == 200
    student_payload = student_analytics.json()
    assert student_payload["total_score"] == 243.0
    assert student_payload["class_rank"] == 1
    assert student_payload["grade_rank"] == 1

    class_analytics = client.get(f"/api/analytics/classes/1?exam_id={exam_id}")
    assert class_analytics.status_code == 200
    class_payload = class_analytics.json()
    assert class_payload["student_count"] == 2
    assert class_payload["total_average"] == 236.5
    assert len(class_payload["subject_breakdown"]) == 2

    teacher_analytics = client.get(f"/api/analytics/teachers/1?exam_id={exam_id}")
    assert teacher_analytics.status_code == 200
    teacher_payload = teacher_analytics.json()
    assert teacher_payload["teacher_name"] == "李语文"
    assert len(teacher_payload["assignment_breakdown"]) == 1
    assert teacher_payload["assignment_breakdown"][0]["average_score"] == 114.0

