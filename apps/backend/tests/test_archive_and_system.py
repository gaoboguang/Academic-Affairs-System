from __future__ import annotations


def test_growth_archive_upload_and_report_export(client) -> None:
    upload_response = client.post(
        "/api/files/upload",
        data={"category": "growth_archive"},
        files={"file": ("note.txt", b"growth attachment", "text/plain")},
    )
    assert upload_response.status_code == 200
    file_payload = upload_response.json()
    assert file_payload["original_filename"] == "note.txt"

    create_response = client.post(
        "/api/archives/students/1/records",
        json={
            "occurred_on": "2026-04-01",
            "record_type": "reward",
            "title": "市级作文竞赛二等奖",
            "content": "表现稳定，获得奖励。",
            "owner_name": "班主任",
            "note": "纳入成长档案",
            "attachment_file_ids": [file_payload["id"]],
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    record_payload = create_response.json()
    assert record_payload["student_id"] == 1
    assert len(record_payload["attachments"]) == 1

    list_response = client.get("/api/archives/students/1/records")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["title"] == "市级作文竞赛二等奖"

    export_response = client.get("/api/archives/students/1/summary/export")
    assert export_response.status_code == 200
    assert "growth_summary_report" in export_response.headers["content-disposition"]

    report_response = client.post(
        "/api/reports/export",
        json={"report_type": "growth_summary", "student_id": 1},
    )
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["report_name"] == "学生成长档案摘要"

    report_download = client.get(report_payload["download_url"])
    assert report_download.status_code == 200


def test_backup_restore_roundtrip(client) -> None:
    initial_students = client.get("/api/students?page=1&page_size=200")
    assert initial_students.status_code == 200
    initial_total = initial_students.json()["total"]

    backup_response = client.post("/api/system/backup")
    assert backup_response.status_code == 200
    backup_id = backup_response.json()["backup_id"]

    create_response = client.post(
        "/api/students",
        json={
            "student_no": "2099001",
            "name": "测试恢复学生",
            "gender": "男",
            "birth_date": None,
            "id_number": None,
            "admission_year": 2024,
            "current_grade_id": 1,
            "current_class_id": 1,
            "status": "active",
            "student_type": "general",
            "art_track": None,
            "phone": None,
            "address": None,
            "note": None,
            "guardians": [],
            "is_active": True,
        },
    )
    assert create_response.status_code == 200

    after_create = client.get("/api/students?page=1&page_size=200")
    assert after_create.status_code == 200
    assert after_create.json()["total"] == initial_total + 1

    restore_response = client.post(
        "/api/system/restore",
        json={"backup_id": backup_id, "auto_backup_current": False},
    )
    assert restore_response.status_code == 200

    after_restore = client.get("/api/students?page=1&page_size=200")
    assert after_restore.status_code == 200
    restored_payload = after_restore.json()
    assert restored_payload["total"] == initial_total
    assert all(item["student_no"] != "2099001" for item in restored_payload["items"])
