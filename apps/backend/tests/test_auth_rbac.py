from __future__ import annotations

from datetime import date
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select

from app.core.security import hash_password
from app.models import AppUser, AuditLog, Exam, ExamSubject, ScoreRecord, Semester, Student


def _seed_user(
    app,
    *,
    username: str,
    password: str,
    role: str,
    teacher_id: int | None = None,
    must_change_password: bool = False,
    is_active: bool = True,
) -> None:
    with app.state.db.session_scope() as session:
        session.add(
            AppUser(
                username=username,
                display_name=username,
                role=role,
                teacher_id=teacher_id,
                password_hash=hash_password(password),
                must_change_password=must_change_password,
                is_active=is_active,
            )
        )


def _login(client, username: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    client.headers.update({"X-CSRF-Token": payload["csrf_token"]})
    return payload


def test_login_sets_cookie_and_returns_current_user(anonymous_client) -> None:
    payload = _login(anonymous_client, "admin", "AdminPass123!")

    assert payload["user"]["username"] == "admin"
    assert payload["user"]["role"] == "admin"
    assert payload["csrf_token"]
    assert "system:manage" in payload["permissions"]
    set_cookie = anonymous_client.cookies.get("local_edu_session")
    assert set_cookie

    me_response = anonymous_client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["username"] == "admin"


def test_unsafe_requests_require_csrf_header(anonymous_client) -> None:
    payload = _login(anonymous_client, "admin", "AdminPass123!")

    denied_response = anonymous_client.post("/api/auth/logout", headers={"X-CSRF-Token": "bad-token"})
    assert denied_response.status_code == 403
    assert denied_response.json()["detail"] == "CSRF 校验失败，请刷新页面后重试"

    allowed_response = anonymous_client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": payload["csrf_token"]},
    )
    assert allowed_response.status_code == 200


def test_login_uses_generic_failure_for_wrong_or_disabled_account(anonymous_client) -> None:
    _seed_user(anonymous_client.app, username="disabled", password="AdminPass123!", role="admin", is_active=False)

    wrong_response = anonymous_client.post("/api/auth/login", json={"username": "missing", "password": "bad"})
    disabled_response = anonymous_client.post(
        "/api/auth/login", json={"username": "disabled", "password": "AdminPass123!"}
    )

    assert wrong_response.status_code == 401
    assert disabled_response.status_code == 401
    assert wrong_response.json()["detail"] == "账号或密码错误"
    assert disabled_response.json()["detail"] == "账号或密码错误"


def test_admin_can_create_reset_disable_and_enable_teacher_account(auth_client) -> None:
    create_response = auth_client.post(
        "/api/admin/users",
        json={
            "username": "teacher01",
            "display_name": "测试教师账号",
            "role": "teacher",
            "teacher_id": 1,
            "extra_class_ids": [2],
        },
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["user"]["username"] == "teacher01"
    assert created["user"]["must_change_password"] is True
    assert created["temporary_password"]

    teacher_login = _login(auth_client, "teacher01", created["temporary_password"])
    assert teacher_login["user"]["must_change_password"] is True

    _login(auth_client, "admin", "AdminPass123!")

    reset_response = auth_client.post(f"/api/admin/users/{created['user']['id']}/reset-password")
    assert reset_response.status_code == 200
    assert reset_response.json()["temporary_password"]

    disable_response = auth_client.post(f"/api/admin/users/{created['user']['id']}/disable")
    assert disable_response.status_code == 200
    assert disable_response.json()["is_active"] is False

    enable_response = auth_client.post(f"/api/admin/users/{created['user']['id']}/enable")
    assert enable_response.status_code == 200
    assert enable_response.json()["is_active"] is True


def test_admin_can_import_teacher_accounts(auth_client) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["账号", "显示名称", "教师工号", "教师姓名", "额外可访问班级"])
    sheet.append(["teacher02", "王数学账号", "T002", "王数学", "高一1班"])
    sheet.append(["teacher02", "重复账号", "T002", "王数学", ""])
    sheet.append(["missing_teacher", "缺少教师", "T999", "不存在", ""])
    buffer = BytesIO()
    workbook.save(buffer)

    response = auth_client.post(
        "/api/admin/users/import",
        data={"strategy": "skip_existing"},
        files={
            "file": (
                "teacher_accounts.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 3
    assert payload["success_rows"] == 1
    assert payload["skipped_rows"] == 1
    assert payload["failed_rows"] == 1
    assert payload["created_accounts"][0]["username"] == "teacher02"
    assert payload["created_accounts"][0]["teacher_no"] == "T002"
    assert payload["created_accounts"][0]["temporary_password"]
    assert "教师工号不存在" in payload["error_preview"][0]

    teacher_login = _login(auth_client, "teacher02", payload["created_accounts"][0]["temporary_password"])
    assert teacher_login["user"]["teacher_name"] == "王数学"
    assert teacher_login["user"]["must_change_password"] is True


def test_teacher_only_sees_and_updates_students_in_owned_classes(anonymous_client) -> None:
    _seed_user(
        anonymous_client.app,
        username="teacher",
        password="TeacherPass123!",
        role="teacher",
        teacher_id=1,
    )
    _login(anonymous_client, "teacher", "TeacherPass123!")

    list_response = anonymous_client.get("/api/students?page=1&page_size=100")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 2
    assert {item["student_no"] for item in payload["items"]} == {"2026001", "2026002"}

    denied_response = anonymous_client.get("/api/students/3")
    assert denied_response.status_code == 403
    assert denied_response.json()["detail"] == "无权访问该学生"

    allowed_response = anonymous_client.put(
        "/api/students/1",
        json={
            "student_no": "2026001",
            "name": "张三",
            "gender": "男",
            "admission_year": 2024,
            "current_grade_id": 1,
            "current_class_id": 1,
            "status": "active",
            "student_type": "general",
            "phone": "13800009999",
            "guardians": [],
            "is_active": True,
        },
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["phone"] == "13800009999"

    with anonymous_client.app.state.db.session_scope() as session:
        student = session.scalar(select(Student).where(Student.id == 1))
        assert student is not None
        assert student.phone == "13800009999"
        audit_log = session.scalar(select(AuditLog).where(AuditLog.actor_username == "teacher"))
        assert audit_log is not None


def test_teacher_cannot_use_admin_only_student_bulk_operations(anonymous_client) -> None:
    _seed_user(
        anonymous_client.app,
        username="teacher",
        password="TeacherPass123!",
        role="teacher",
        teacher_id=1,
    )
    _login(anonymous_client, "teacher", "TeacherPass123!")

    response = anonymous_client.post(
        "/api/students/bulk-delete/preview",
        json={"student_ids": [1], "mode": "soft_delete", "reason": "测试"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "需要管理员权限"


def test_teacher_score_import_rejects_students_outside_owned_classes(anonymous_client) -> None:
    _seed_user(
        anonymous_client.app,
        username="teacher",
        password="TeacherPass123!",
        role="teacher",
        teacher_id=1,
    )
    with anonymous_client.app.state.db.session_scope() as session:
        semester = session.scalar(select(Semester).where(Semester.is_current.is_(True)))
        assert semester is not None
        exam = Exam(
            name="教师范围导入测试",
            exam_type="月考",
            exam_date=date(2026, 5, 1),
            semester_id=semester.id,
            grade_scope_json=[1],
            status="published",
        )
        session.add(exam)
        session.flush()
        session.add(ExamSubject(exam_id=exam.id, subject_id=1, full_score=150, sort_order=1))
        exam_id = exam.id

    _login(anonymous_client, "teacher", "TeacherPass123!")
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["考试名称", "学号", "姓名", "班级", "科目", "分数", "缺考标记", "备注"])
    sheet.append(["教师范围导入测试", "2026001", "张三", "1班", "语文", 120, "", ""])
    sheet.append(["教师范围导入测试", "2026003", "王五", "2班", "语文", 110, "", ""])
    buffer = BytesIO()
    workbook.save(buffer)

    response = anonymous_client.post(
        f"/api/exams/{exam_id}/scores/import",
        data={"strategy": "overwrite", "rebuild": "false"},
        files={"file": ("scores.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success_rows"] == 1
    assert payload["failed_rows"] == 1
    assert "无权导入该学生成绩" in payload["error_preview"][0]

    with anonymous_client.app.state.db.session_scope() as session:
        imported_records = session.scalars(select(ScoreRecord).where(ScoreRecord.exam_id == exam_id)).all()
        assert [(item.student_id, item.score) for item in imported_records] == [(1, 120)]
