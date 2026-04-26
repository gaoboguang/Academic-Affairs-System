from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models import (
    AuditLog,
    SchoolClass,
    Student,
    StudentClassHistory,
    StudentClassTransferBatch,
    StudentClassTransferItem,
)


def _get_class_id(app, class_name: str) -> int:
    with app.state.db.session_scope() as session:
        school_class = session.scalar(select(SchoolClass).where(SchoolClass.name == class_name))
        assert school_class is not None
        return school_class.id


def test_student_class_transfer_preview_execute_and_history(client) -> None:
    target_class_id = _get_class_id(client.app, "2班")

    preview_response = client.post(
        "/api/students/class-transfer/preview",
        json={
            "student_ids": [1, 2],
            "target_class_id": target_class_id,
            "effective_on": "2026-04-25",
            "reason": "文理方向调整",
            "note": "高一年级统一调班",
            "operator_name": "测试老师",
        },
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["total"] == 2
    assert preview_payload["transferable_count"] == 2
    assert preview_payload["blocked_count"] == 0
    assert preview_payload["required_confirm_text"] == "确认调班 2 名学生"
    assert len(preview_payload["confirm_token"]) == 64
    assert preview_payload["items"][0]["from_class_name"] == "1班"
    assert preview_payload["items"][0]["to_class_name"] == "2班"

    execute_response = client.post(
        "/api/students/class-transfer",
        json={
            "student_ids": [1, 2],
            "target_class_id": target_class_id,
            "effective_on": "2026-04-25",
            "reason": "文理方向调整",
            "note": "高一年级统一调班",
            "operator_name": "测试老师",
            "confirm_token": preview_payload["confirm_token"],
            "confirm_text": preview_payload["required_confirm_text"],
        },
    )
    assert execute_response.status_code == 200
    execute_payload = execute_response.json()
    assert execute_payload["status"] == "success"
    assert execute_payload["success_count"] == 2
    assert execute_payload["failed_count"] == 0
    assert execute_payload["batch_id"] is not None
    assert execute_payload["success_items"][0]["after_snapshot_json"]["current_class_name"] == "2班"

    history_response = client.get("/api/students/1/class-transfer-history")
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert history_payload[0]["event_type"] == "class_transfer"
    assert history_payload[0]["from_class_name"] == "1班"
    assert history_payload[0]["to_class_name"] == "2班"
    assert history_payload[0]["effective_on"] == "2026-04-25"
    assert history_payload[0]["reason"] == "文理方向调整"
    assert "班级调整" in history_payload[0]["summary"]

    with client.app.state.db.session_scope() as session:
        student = session.scalar(select(Student).where(Student.id == 1))
        assert student is not None
        assert student.current_class_id == target_class_id
        target_class = session.scalar(select(SchoolClass).where(SchoolClass.id == target_class_id))
        assert target_class is not None
        assert student.current_grade_id == target_class.grade_id

        class_one = session.scalar(select(SchoolClass).where(SchoolClass.name == "1班"))
        class_two = session.scalar(select(SchoolClass).where(SchoolClass.name == "2班"))
        assert class_one is not None
        assert class_two is not None
        assert class_one.student_count == 0
        assert class_two.student_count == 3

        batch = session.scalar(select(StudentClassTransferBatch).where(StudentClassTransferBatch.id == execute_payload["batch_id"]))
        assert batch is not None
        assert batch.status == "success"
        assert batch.success_count == 2
        assert batch.reason == "文理方向调整"
        transfer_item = session.scalar(
            select(StudentClassTransferItem).where(
                StudentClassTransferItem.batch_id == batch.id,
                StudentClassTransferItem.student_id == 1,
            )
        )
        assert transfer_item is not None
        assert transfer_item.status == "success"
        open_history = session.scalar(
            select(StudentClassHistory).where(
                StudentClassHistory.student_id == 1,
                StudentClassHistory.class_id == target_class_id,
                StudentClassHistory.end_date.is_(None),
            )
        )
        assert open_history is not None
        assert open_history.start_date == date(2026, 4, 25)
        assert open_history.reason == "调班：文理方向调整"
        audit_log = session.scalar(
            select(AuditLog).where(AuditLog.action == "class_transfer").order_by(AuditLog.id.desc())
        )
        assert audit_log is not None
        assert audit_log.detail_json["batch_id"] == batch.id
        assert audit_log.detail_json["success_count"] == 2


def test_student_class_transfer_blocks_student_already_in_target_class(client) -> None:
    target_class_id = _get_class_id(client.app, "2班")

    response = client.post(
        "/api/students/class-transfer/preview",
        json={
            "student_ids": [3],
            "target_class_id": target_class_id,
            "effective_on": "2026-04-25",
            "reason": "测试重复调班",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["transferable_count"] == 0
    assert payload["blocked_count"] == 1
    assert payload["blocked"][0]["reason"] == "学生已在目标班级"


def test_student_class_transfer_rejects_missing_target_class(client) -> None:
    response = client.post(
        "/api/students/class-transfer/preview",
        json={
            "student_ids": [1],
            "target_class_id": 9999,
            "effective_on": "2026-04-25",
            "reason": "测试目标班级不存在",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "目标班级不存在"
