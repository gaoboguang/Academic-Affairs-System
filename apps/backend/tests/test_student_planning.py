from __future__ import annotations


def test_student_planning_goal_task_note_and_reports(client) -> None:
    student_id = 1

    empty_response = client.get(f"/api/planning/students/{student_id}")
    assert empty_response.status_code == 200
    empty_payload = empty_response.json()
    assert empty_payload["summary"]["no_goal"] is True
    assert any(item["title"] == "建立学生升学目标" for item in empty_payload["suggested_tasks"])

    goal_response = client.post(
        "/api/planning/goals",
        json={
            "student_id": student_id,
            "target_year": 2026,
            "pathway_code": "summer_general_regular",
            "pathway_name": "普通类常规批",
            "target_college": "山东大学",
            "target_major": "计算机类",
            "target_score": 620,
            "target_rank": 12000,
            "backup_pathways": "综评 / 春考",
        },
    )
    assert goal_response.status_code == 200
    goal = goal_response.json()
    assert goal["status_label"] == "进行中"

    task_response = client.post(
        "/api/planning/tasks",
        json={
            "student_id": student_id,
            "goal_id": goal["id"],
            "task_type": "chapter_review",
            "title": "复核山东大学计算机类章程",
            "priority": "high",
            "due_date": "2026-04-27",
        },
    )
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["is_overdue"] is True

    complete_response = client.put(f"/api/planning/tasks/{task['id']}", json={"status": "completed"})
    assert complete_response.status_code == 200
    assert complete_response.json()["completed_at"]

    note_response = client.post(
        "/api/planning/notes",
        json={
            "student_id": student_id,
            "goal_id": goal["id"],
            "content": "已与家长确认目标路径，下周复核章程。",
        },
    )
    assert note_response.status_code == 200
    assert note_response.json()["note_type_label"] == "复盘"

    planning_response = client.get(f"/api/planning/students/{student_id}")
    assert planning_response.status_code == 200
    planning = planning_response.json()
    assert planning["summary"]["no_goal"] is False
    assert planning["summary"]["completed_task_count"] == 1
    assert planning["notes"][0]["content"].startswith("已与家长确认")

    report_response = client.post(
        "/api/reports/export",
        json={
            "report_type": "planning_followup",
            "student_id": student_id,
        },
    )
    assert report_response.status_code == 200
    assert report_response.json()["download_url"]

    explicit_report_response = client.post(
        "/api/reports/planning-followup/export",
        json={"student_id": student_id},
    )
    assert explicit_report_response.status_code == 200
    assert explicit_report_response.json()["download_url"]


def test_bulk_create_planning_tasks_from_pathway_material_gaps(client) -> None:
    student_id = 1
    client.post("/api/gaokao/pathways/bootstrap-shandong", params={"target_year": 2026})
    profile_response = client.put(
        f"/api/gaokao/students/{student_id}/pathway-profile",
        json={
            "province": "山东",
            "candidate_type": "general",
            "has_gaokao_registration": True,
            "subject_combination": "物理,化学,生物",
            "materials_json": {},
        },
    )
    assert profile_response.status_code == 200

    response = client.post(
        "/api/planning/tasks/bulk-create-from-pathway",
        json={
            "student_id": student_id,
            "target_year": 2026,
            "include_material_gaps": True,
            "include_review_tasks": True,
            "due_date": "2026-05-10",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["created_count"] >= 1
    assert any(item["task_type"] in {"material", "chapter_review"} for item in payload["tasks"])

    second_response = client.post(
        "/api/planning/tasks/bulk-create-from-pathway",
        json={
            "student_id": student_id,
            "target_year": 2026,
            "include_material_gaps": True,
            "include_review_tasks": True,
            "due_date": "2026-05-10",
        },
    )
    assert second_response.status_code == 200
    assert second_response.json()["created_count"] == 0
    assert second_response.json()["skipped_count"] >= payload["created_count"]

    dashboard_response = client.get("/api/dashboard/summary")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["planning_summary"]["open_task_count"] >= payload["created_count"]
