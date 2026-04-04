from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


def build_score_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["考试名称", "学号", "姓名", "班级", "科目", "分数", "缺考标记", "备注"])
    sheet.append(["2026届高一5月月考", "2026001", "张三", "1班", "语文", "120", "", ""])
    sheet.append(["2026届高一5月月考", "2026001", "张三", "1班", "数学", "128", "", ""])
    sheet.append(["2026届高一5月月考", "2026002", "李四", "1班", "语文", "112", "", ""])
    sheet.append(["2026届高一5月月考", "2026002", "李四", "1班", "数学", "118", "", ""])
    sheet.append(["2026届高一5月月考", "2026003", "王五", "2班", "语文", "95", "", ""])
    sheet.append(["2026届高一5月月考", "2026003", "王五", "2班", "数学", "100", "", ""])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def create_exam_with_scores(client) -> int:
    exam_response = client.post(
        "/api/exams",
        json={
            "name": "2026届高一5月月考",
            "exam_type": "月考",
            "exam_date": "2026-05-10",
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


def test_grade_analytics_and_student_attachment_management(client) -> None:
    exam_id = create_exam_with_scores(client)

    grade_response = client.get(f"/api/analytics/grades/1?exam_id={exam_id}")
    assert grade_response.status_code == 200
    grade_payload = grade_response.json()
    assert grade_payload["grade_name"] == "高一"
    assert grade_payload["student_count"] == 3
    assert len(grade_payload["class_breakdown"]) == 2
    assert len(grade_payload["subject_breakdown"]) == 2
    assert sum(item["count"] for item in grade_payload["score_bands"]) == 3

    upload_response = client.post(
        "/api/files/upload",
        data={"category": "student_attachment"},
        files={"file": ("photo.jpg", b"binary-data", "image/jpeg")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    create_attachment_response = client.post(
        "/api/students/1/attachments",
        json={
            "stored_file_id": file_id,
            "attachment_type": "证件",
            "title": "学生照片",
            "note": "用于学籍核验",
            "is_active": True,
        },
    )
    assert create_attachment_response.status_code == 200
    attachment_payload = create_attachment_response.json()
    assert attachment_payload["title"] == "学生照片"
    assert attachment_payload["source_type"] == "student_attachment"

    list_attachment_response = client.get("/api/students/1/attachments")
    assert list_attachment_response.status_code == 200
    attachments = list_attachment_response.json()
    assert len(attachments) == 1
    assert attachments[0]["attachment_type"] == "证件"

    profile_response = client.get("/api/students/1/profile")
    assert profile_response.status_code == 200
    profile_payload = profile_response.json()
    assert any(item["title"] == "学生照片" for item in profile_payload["attachments"])

    delete_attachment_response = client.delete(f"/api/students/1/attachments/{attachment_payload['id']}")
    assert delete_attachment_response.status_code == 200
    assert delete_attachment_response.json()["message"] == "学生附件已删除"

    list_after_delete_response = client.get("/api/students/1/attachments")
    assert list_after_delete_response.status_code == 200
    assert list_after_delete_response.json() == []
