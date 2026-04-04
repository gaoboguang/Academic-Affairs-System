from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook


def build_evaluation_workbook(rows: list[list[object]] | None = None) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["模板名称", "教师", "班级", "题目", "分值", "评价对象类型"])
    rows = rows or [
        ["通用课堂评教模板", "李语文", "1班", "教学目标清晰，重难点明确", 5, "学生"],
        ["通用课堂评教模板", "李语文", "1班", "课堂节奏合理，互动有效", 4, "学生"],
        ["通用课堂评教模板", "李语文", "1班", "作业讲评及时，反馈有针对性", 5, "学生"],
        ["通用课堂评教模板", "王数学", "2班", "教学目标清晰，重难点明确", 4, "学生"],
        ["通用课堂评教模板", "王数学", "2班", "课堂节奏合理，互动有效", 4, "学生"],
        ["通用课堂评教模板", "王数学", "2班", "作业讲评及时，反馈有针对性", 3, "学生"],
    ]
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_evaluation_and_adviser_quant_workflow(client) -> None:
    templates_response = client.get("/api/evaluation/templates")
    assert templates_response.status_code == 200
    templates_payload = templates_response.json()
    assert len(templates_payload) >= 1
    template_id = templates_payload[0]["id"]

    import_response = client.post(
        "/api/evaluation/import",
        data={"template_id": template_id, "semester_id": 2},
        files={
            "file": (
                "evaluation.xlsx",
                build_evaluation_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert import_response.status_code == 200
    import_payload = import_response.json()
    assert import_payload["success_rows"] == 6
    batch_id = import_payload["batch_id"]

    second_import_response = client.post(
        "/api/evaluation/import",
        data={"template_id": template_id, "semester_id": 2},
        files={
            "file": (
                "evaluation_round2.xlsx",
                build_evaluation_workbook(
                    [
                        ["通用课堂评教模板", "李语文", "1班", "教学目标清晰，重难点明确", 4, "学生"],
                        ["通用课堂评教模板", "李语文", "1班", "课堂节奏合理，互动有效", 4, "学生"],
                        ["通用课堂评教模板", "李语文", "1班", "作业讲评及时，反馈有针对性", 4, "学生"],
                        ["通用课堂评教模板", "王数学", "2班", "教学目标清晰，重难点明确", 5, "学生"],
                        ["通用课堂评教模板", "王数学", "2班", "课堂节奏合理，互动有效", 5, "学生"],
                        ["通用课堂评教模板", "王数学", "2班", "作业讲评及时，反馈有针对性", 4, "学生"],
                    ]
                ),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert second_import_response.status_code == 200
    second_batch_id = second_import_response.json()["batch_id"]

    overview_response = client.get(f"/api/evaluation/batches/{batch_id}/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["teacher_count"] == 2
    assert overview_payload["teacher_summaries"][0]["teacher_name"] == "李语文"

    compare_response = client.get(f"/api/evaluation/batches/{second_batch_id}/compare?compare_batch_id={batch_id}")
    assert compare_response.status_code == 200
    compare_payload = compare_response.json()
    assert compare_payload["overlap_teacher_count"] == 2
    assert compare_payload["improved_count"] == 1
    assert compare_payload["declined_count"] == 1
    assert compare_payload["teacher_deltas"][0]["teacher_name"] == "王数学"

    detail_response = client.get(f"/api/evaluation/batches/{batch_id}/teachers/1")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["dimension_summaries"]) == 3

    trend_response = client.get(f"/api/evaluation/teachers/1/trend?template_id={template_id}")
    assert trend_response.status_code == 200
    trend_payload = trend_response.json()
    assert len(trend_payload["points"]) == 2
    assert trend_payload["points"][0]["overall_avg_score"] == 93.33
    assert trend_payload["points"][1]["overall_avg_score"] == 80.0

    upload_response = client.post(
        "/api/files/upload",
        data={"category": "adviser_quant"},
        files={"file": ("proof.txt", b"proof", "text/plain")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    rule_versions_response = client.get("/api/adviser-quant/rules")
    assert rule_versions_response.status_code == 200
    rule_version_payload = rule_versions_response.json()
    assert len(rule_version_payload) >= 1
    rule_version_id = rule_version_payload[0]["id"]

    rule_items_response = client.get(f"/api/adviser-quant/rules/{rule_version_id}/items")
    assert rule_items_response.status_code == 200
    rule_items_payload = rule_items_response.json()
    attachment_item = next(item for item in rule_items_payload if item["requires_attachment"])

    record_response = client.post(
        "/api/adviser-quant/records",
        json={
            "teacher_id": 1,
            "class_id": 1,
            "semester_id": 2,
            "rule_item_id": attachment_item["id"],
            "record_month": "2026-04",
            "score": 4.5,
            "description": "完成家校沟通与回访",
            "attachment_file_ids": [file_id],
            "is_active": True,
        },
    )
    assert record_response.status_code == 200
    record_payload = record_response.json()
    assert record_payload["attachments"][0]["stored_file_id"] == file_id

    summary_response = client.get(f"/api/adviser-quant/summary?semester_id=2&rule_version_id={rule_version_id}")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert len(summary_payload) == 1
    assert summary_payload[0]["teacher_name"] == "李语文"

    evaluation_report_response = client.post(
        "/api/reports/export",
        json={"report_type": "evaluation_summary", "batch_id": batch_id},
    )
    assert evaluation_report_response.status_code == 200

    quant_report_response = client.post(
        "/api/reports/export",
        json={
            "report_type": "adviser_quant_summary",
            "semester_id": 2,
            "rule_version_id": rule_version_id,
        },
    )
    assert quant_report_response.status_code == 200
