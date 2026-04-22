from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from app.models import Subject


def build_teacher_import_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["工号", "姓名", "性别", "学科", "联系方式", "职称", "岗位", "是否班主任", "任教状态", "入职日期", "备注"])
    sheet.append(["T100", "测试教师", "女", "语文", "13800000000", "一级教师", "学科教师", "是", "在岗", "2022-08-01", ""])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_health_endpoint(client) -> None:
    response = client.get("/api/system/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_student_and_list(client) -> None:
    class_response = client.post(
        "/api/base/classes",
        json={
            "grade_id": 1,
            "name": "9班",
            "class_type": "normal",
            "head_teacher_id": None,
            "student_count": 0,
            "is_active": True,
        },
    )
    assert class_response.status_code == 200
    class_id = class_response.json()["id"]

    create_response = client.post(
        "/api/students",
        json={
            "student_no": "2026999",
            "name": "接口学生",
            "gender": "女",
            "birth_date": "2009-05-01",
            "admission_year": 2024,
            "current_grade_id": 1,
            "current_class_id": class_id,
            "status": "active",
            "student_type": "general",
            "art_track": None,
            "origin_province": "广东",
            "phone": "13812345678",
            "address": "测试地址",
            "note": "接口测试",
            "guardians": [],
            "is_active": True,
        },
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["student_no"] == "2026999"
    assert payload["current_class_name"] == "9班"
    assert payload["origin_province"] == "广东"

    list_response = client.get("/api/students?page=1&page_size=20&student_no=2026999")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1


def test_base_subjects_include_small_language_options(client) -> None:
    with client.app.state.db.session_scope() as session:
        session.query(Subject).where(Subject.code.in_(["japanese", "russian"])).delete(synchronize_session=False)

    response = client.get("/api/base/subjects")
    assert response.status_code == 200

    payload = response.json()
    subject_codes = {item["code"] for item in payload}
    subject_names = {item["name"] for item in payload}
    assert {"japanese", "russian"}.issubset(subject_codes)
    assert {"日语", "俄语"}.issubset(subject_names)


def test_import_teacher_and_create_assignment(client) -> None:
    import_response = client.post(
        "/api/teachers/import",
        data={"strategy": "skip_existing"},
        files={
            "file": (
                "teachers.xlsx",
                build_teacher_import_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert import_response.status_code == 200
    import_payload = import_response.json()
    assert import_payload["success_rows"] == 1
    assert import_payload["failed_rows"] == 0

    teachers_response = client.get("/api/teachers?page=1&page_size=20&teacher_no=T100")
    assert teachers_response.status_code == 200
    teacher_id = teachers_response.json()["items"][0]["id"]

    assignment_response = client.post(
        "/api/teachers/assignments",
        json={
            "teacher_id": teacher_id,
            "semester_id": 2,
            "grade_id": 1,
            "class_id": None,
            "subject_id": 1,
            "course_type": "regular",
            "weekly_periods_manual": 4,
            "is_active": True,
        },
    )

    assert assignment_response.status_code == 200
    assert assignment_response.json()["teacher_name"] == "测试教师"
