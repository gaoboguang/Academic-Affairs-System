from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models import (
    AuditLog,
    College,
    Exam,
    GaokaoPathway,
    Major,
    RecommendationResult,
    RecommendationScheme,
    SchoolClass,
    ScoreRecord,
    ScoreSubjectSnapshot,
    ScoreTotalSnapshot,
    Semester,
    StoredFile,
    Student,
    StudentAttachment,
    StudentClassHistory,
    StudentGaokaoScoreProjection,
    StudentGrowthRecord,
    StudentPathwayEvaluation,
    StudentPathwayProfile,
    VolunteerDraft,
)


def _seed_bulk_delete_related_data(app) -> int:
    with app.state.db.session_scope() as session:
        semester = session.scalar(select(Semester).where(Semester.is_current.is_(True)))
        assert semester is not None
        exam = Exam(
            name="批量删除关联测试",
            exam_type="月考",
            exam_date=date(2026, 4, 26),
            semester_id=semester.id,
            grade_scope_json=[1],
            status="published",
        )
        session.add(exam)
        session.flush()

        session.add_all(
            [
                ScoreRecord(exam_id=exam.id, student_id=1, subject_id=1, score=120),
                ScoreTotalSnapshot(exam_id=exam.id, student_id=1, total_score=120),
                ScoreSubjectSnapshot(exam_id=exam.id, student_id=1, subject_id=1, score=120),
                StudentGrowthRecord(
                    student_id=1,
                    occurred_on=date(2026, 4, 26),
                    record_type="award",
                    title="批量删除前保留的成长记录",
                ),
                StudentClassHistory(
                    student_id=1,
                    grade_id=1,
                    class_id=1,
                    start_date=date(2025, 9, 1),
                    reason="入学分班",
                ),
            ]
        )
        stored_file = StoredFile(
            original_filename="bulk-delete.txt",
            file_path="uploads/bulk-delete.txt",
            file_size=10,
            category="student_attachment",
        )
        session.add(stored_file)
        session.flush()
        session.add(
            StudentAttachment(
                student_id=1,
                stored_file_id=stored_file.id,
                attachment_type="证明",
                title="批量删除前保留的附件",
            )
        )

        scheme = RecommendationScheme(
            name="批量删除关联方案",
            target_year=2026,
            province="山东",
            student_type="general",
        )
        college = College(name="批量删除测试大学", province="山东")
        major = Major(name="批量删除测试专业")
        session.add_all([scheme, college, major])
        session.flush()
        session.add(
            RecommendationResult(
                student_id=1,
                exam_id=exam.id,
                scheme_id=scheme.id,
                result_type="safe",
                college_id=college.id,
                major_id=major.id,
                score_basis="rank",
            )
        )
        session.add(
            VolunteerDraft(
                name="批量删除前保留的志愿草稿",
                student_id=1,
                exam_id=exam.id,
                province="山东",
                target_year=2026,
                candidate_type="general",
                score_input_mode="manual_rank",
                risk_preference="balanced",
            )
        )
        session.add(
            StudentGaokaoScoreProjection(
                student_id=1,
                target_year=2026,
                province="山东",
                source_mode="manual",
                confidence_level="medium",
            )
        )
        session.add(
            StudentPathwayProfile(
                student_id=1,
                province="山东",
                candidate_type="general",
            )
        )
        pathway = GaokaoPathway(
            province="山东",
            pathway_code="bulk_delete_test_pathway",
            pathway_name="批量删除测试路径",
            pathway_group="测试路径",
            recommendation_depth="资格初筛",
            status="active",
        )
        session.add(pathway)
        session.flush()
        session.add(
            StudentPathwayEvaluation(
                student_id=1,
                pathway_id=pathway.id,
                target_year=2026,
                status="unknown",
                status_label="信息不足",
                confidence_level="low",
                recommendation_depth="资格初筛",
            )
        )
        return exam.id


def test_student_bulk_delete_preview_and_execute_soft_deletes_only(client) -> None:
    _seed_bulk_delete_related_data(client.app)

    preview_response = client.post(
        "/api/students/bulk-delete/preview",
        json={
            "student_ids": [1, 9999],
            "mode": "soft_delete",
            "reason": "误导入重复学生",
            "operator_name": "测试老师",
        },
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["total"] == 2
    assert preview_payload["deletable_count"] == 1
    assert preview_payload["blocked_count"] == 1
    assert preview_payload["required_confirm_text"] == "确认删除 1 名学生"
    assert len(preview_payload["confirm_token"]) == 64
    warning_counts = preview_payload["warnings"][0]["association_counts"]
    assert warning_counts["score_count"] == 1
    assert warning_counts["score_snapshot_count"] == 2
    assert warning_counts["growth_record_count"] == 1
    assert warning_counts["attachment_count"] == 1
    assert warning_counts["class_history_count"] == 1
    assert warning_counts["recommendation_count"] == 1
    assert warning_counts["volunteer_draft_count"] == 1
    assert warning_counts["gaokao_score_projection_count"] == 1
    assert warning_counts["pathway_profile_count"] == 1
    assert warning_counts["pathway_evaluation_count"] == 1
    assert preview_payload["blocked"][0]["reason"] == "学生不存在或已停用"

    execute_response = client.post(
        "/api/students/bulk-delete",
        json={
            "student_ids": [1, 9999],
            "mode": "soft_delete",
            "reason": "误导入重复学生",
            "operator_name": "测试老师",
            "confirm_token": preview_payload["confirm_token"],
            "confirm_text": preview_payload["required_confirm_text"],
        },
    )
    assert execute_response.status_code == 200
    execute_payload = execute_response.json()
    assert execute_payload["status"] == "partially_failed"
    assert execute_payload["success_count"] == 1
    assert execute_payload["failed_count"] == 1
    assert execute_payload["blocked_count"] == 1
    assert execute_payload["success_items"][0]["after_snapshot_json"]["is_active"] is False
    assert execute_payload["blocked"][0]["error_message"] == "学生不存在或已停用"

    list_response = client.get("/api/students?page=1&page_size=100")
    assert list_response.status_code == 200
    assert all(item["id"] != 1 for item in list_response.json()["items"])

    inactive_list_response = client.get("/api/students?page=1&page_size=100&include_inactive=true")
    assert inactive_list_response.status_code == 200
    inactive_student = next(item for item in inactive_list_response.json()["items"] if item["id"] == 1)
    assert inactive_student["is_active"] is False

    detail_response = client.get("/api/students/1")
    assert detail_response.status_code == 200
    assert detail_response.json()["is_active"] is False

    with client.app.state.db.session_scope() as session:
        assert session.scalar(select(Student).where(Student.id == 1)).is_active is False
        assert session.scalar(select(ScoreRecord).where(ScoreRecord.student_id == 1)) is not None
        assert session.scalar(select(StudentGrowthRecord).where(StudentGrowthRecord.student_id == 1)) is not None
        assert session.scalar(select(StudentAttachment).where(StudentAttachment.student_id == 1)) is not None
        assert session.scalar(select(RecommendationResult).where(RecommendationResult.student_id == 1)) is not None
        assert session.scalar(select(VolunteerDraft).where(VolunteerDraft.student_id == 1)) is not None
        assert session.scalar(select(StudentPathwayProfile).where(StudentPathwayProfile.student_id == 1)) is not None
        assert session.scalar(select(StudentPathwayEvaluation).where(StudentPathwayEvaluation.student_id == 1)) is not None
        assert session.scalar(select(SchoolClass).where(SchoolClass.id == 1)).student_count == 1
        audit_log = session.scalar(
            select(AuditLog).where(AuditLog.action == "bulk_delete").order_by(AuditLog.id.desc())
        )
        assert audit_log is not None
        assert audit_log.detail_json["success_count"] == 1
        assert audit_log.detail_json["failed_count"] == 1


def test_student_bulk_delete_requires_fresh_preview_and_confirm_text(client) -> None:
    preview_response = client.post(
        "/api/students/bulk-delete/preview",
        json={
            "student_ids": [1],
            "mode": "soft_delete",
            "reason": "测试确认保护",
        },
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()

    bad_token_response = client.post(
        "/api/students/bulk-delete",
        json={
            "student_ids": [1],
            "mode": "soft_delete",
            "reason": "测试确认保护",
            "confirm_token": "invalid-token-value",
            "confirm_text": preview_payload["required_confirm_text"],
        },
    )
    assert bad_token_response.status_code == 400
    assert bad_token_response.json()["detail"] == "删除确认已过期，请重新预检后再执行"

    bad_text_response = client.post(
        "/api/students/bulk-delete",
        json={
            "student_ids": [1],
            "mode": "soft_delete",
            "reason": "测试确认保护",
            "confirm_token": preview_payload["confirm_token"],
            "confirm_text": "确认删除 2 名学生",
        },
    )
    assert bad_text_response.status_code == 400
    assert bad_text_response.json()["detail"] == "确认文字不正确，请输入：确认删除 1 名学生"

    list_response = client.get("/api/students?page=1&page_size=100")
    assert list_response.status_code == 200
    assert any(item["id"] == 1 for item in list_response.json()["items"])
