from __future__ import annotations

from sqlalchemy import select

from app.core.security import hash_password
from app.models import AppUser, AuditLog, Subject


def _seed_user(
    app,
    *,
    username: str,
    password: str,
    role: str,
    teacher_id: int | None = None,
) -> None:
    with app.state.db.session_scope() as session:
        session.add(
            AppUser(
                username=username,
                display_name=username,
                role=role,
                teacher_id=teacher_id,
                password_hash=hash_password(password),
                must_change_password=False,
            )
        )


def _login(client, username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    client.headers.update({"X-CSRF-Token": payload["csrf_token"]})
    return payload


def _subject_id(app, subject_name: str) -> int:
    with app.state.db.session_scope() as session:
        subject = session.scalar(select(Subject).where(Subject.name == subject_name))
        assert subject is not None
        return subject.id


def test_teacher_can_leave_and_list_comment_for_taught_student(anonymous_client) -> None:
    _seed_user(
        anonymous_client.app,
        username="chinese",
        password="TeacherPass123!",
        role="teacher",
        teacher_id=1,
    )
    _login(anonymous_client, "chinese", "TeacherPass123!")
    subject_id = _subject_id(anonymous_client.app, "语文")

    options_response = anonymous_client.get("/api/students/1/teacher-comments")
    assert options_response.status_code == 200
    options_payload = options_response.json()
    assert options_payload["can_comment"] is True
    assert [item["subject_name"] for item in options_payload["available_subjects"]] == ["语文"]

    create_response = anonymous_client.post(
        "/api/students/1/teacher-comments",
        json={"subject_id": subject_id, "content": "课堂发言积极，换班后可继续安排展示型任务。"},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["teacher_name"] == "李语文"
    assert created["subject_name"] == "语文"
    assert created["content"] == "课堂发言积极，换班后可继续安排展示型任务。"

    list_response = anonymous_client.get("/api/students/1/teacher-comments")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["items"][0]["id"] == created["id"]
    assert payload["items"][0]["class_name"] == "1班"

    with anonymous_client.app.state.db.session_scope() as session:
        audit_log = session.scalar(
            select(AuditLog).where(
                AuditLog.module == "students",
                AuditLog.action == "create_teacher_comment",
                AuditLog.actor_username == "chinese",
            )
        )
        assert audit_log is not None


def test_teacher_comment_rejects_student_outside_teacher_scope(anonymous_client) -> None:
    _seed_user(
        anonymous_client.app,
        username="chinese",
        password="TeacherPass123!",
        role="teacher",
        teacher_id=1,
    )
    _login(anonymous_client, "chinese", "TeacherPass123!")
    subject_id = _subject_id(anonymous_client.app, "语文")

    response = anonymous_client.post(
        "/api/students/3/teacher-comments",
        json={"subject_id": subject_id, "content": "这条不应写入范围外学生。"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "无权访问该学生"


def test_unlinked_admin_can_read_but_not_publish_teacher_comment(auth_client) -> None:
    list_response = auth_client.get("/api/students/1/teacher-comments")
    assert list_response.status_code == 200
    assert list_response.json()["can_comment"] is False

    response = auth_client.post(
        "/api/students/1/teacher-comments",
        json={"subject_id": _subject_id(auth_client.app, "语文"), "content": "管理员不应冒充任课教师发布。"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "当前账号未关联教师档案，无法发布教师评语"
