from __future__ import annotations


def test_classes_overview_and_profile_include_teachers_students_and_honors(client) -> None:
    honor_response = client.post(
        "/api/classes/1/honors",
        json={
            "title": "校级先进班集体",
            "honor_level": "校级",
            "awarded_on": "2026-04-20",
            "source": "德育处",
            "note": "月度评比",
            "is_active": True,
        },
    )
    assert honor_response.status_code == 200
    assert honor_response.json()["title"] == "校级先进班集体"

    overview_response = client.get("/api/classes/overview?grade_id=1&semester_id=2")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total_classes"] >= 2
    assert overview["total_students"] >= 3
    assert overview["total_honors"] == 1
    grade_group = next(item for item in overview["grades"] if item["grade_id"] == 1)
    class_one = next(item for item in grade_group["classes"] if item["class_id"] == 1)
    assert class_one["head_teacher_name"] == "李语文"
    assert class_one["teacher_count"] == 2
    assert class_one["active_student_count"] == 2
    assert class_one["latest_honor"]["title"] == "校级先进班集体"
    assert class_one["teaching_complete"] is True

    profile_response = client.get("/api/classes/1/profile?semester_id=2")
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["overview"]["class_name"] == "1班"
    assert len(profile["students"]) == 2
    assert {item["student_no"] for item in profile["students"]} == {"2026001", "2026002"}
    assert len(profile["assignments"]) == 2
    assert profile["honors"][0]["title"] == "校级先进班集体"


def test_class_honor_crud_soft_deletes_and_validates_scope(client) -> None:
    create_response = client.post(
        "/api/classes/1/honors",
        json={
            "title": "卫生流动红旗",
            "honor_level": "年级",
            "awarded_on": "2026-04-01",
            "source": "年级组",
            "note": None,
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    honor_id = create_response.json()["id"]

    duplicate_response = client.post(
        "/api/classes/1/honors",
        json={
            "title": "卫生流动红旗",
            "honor_level": "年级",
            "awarded_on": "2026-04-01",
            "source": "年级组",
            "note": None,
            "is_active": True,
        },
    )
    assert duplicate_response.status_code == 400

    update_response = client.put(
        f"/api/classes/1/honors/{honor_id}",
        json={
            "title": "卫生流动红旗月度奖",
            "honor_level": "年级",
            "awarded_on": "2026-04-01",
            "source": "年级组",
            "note": "更新说明",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "卫生流动红旗月度奖"

    wrong_class_response = client.put(
        f"/api/classes/2/honors/{honor_id}",
        json={
            "title": "错误班级",
            "honor_level": "年级",
            "awarded_on": "2026-04-01",
            "source": "年级组",
            "note": None,
            "is_active": True,
        },
    )
    assert wrong_class_response.status_code == 404

    delete_response = client.delete(f"/api/classes/1/honors/{honor_id}")
    assert delete_response.status_code == 200

    list_response = client.get("/api/classes/1/honors")
    assert list_response.status_code == 200
    assert all(item["id"] != honor_id for item in list_response.json())


def test_grade_profile_returns_class_matrix_with_empty_states(client) -> None:
    response = client.get("/api/grades/1/profile?semester_id=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["grade"]["grade_name"] == "高一"
    assert payload["grade"]["class_count"] >= 2
    class_two = next(item for item in payload["classes"] if item["class_name"] == "2班")
    assert class_two["head_teacher_name"] is None
    assert class_two["teacher_count"] == 0
    assert class_two["honor_count"] == 0
    assert class_two["score_summary"]["sample_count"] == 0
