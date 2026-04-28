from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.exporters.archive import export_growth_summary
from app.exporters.recommendations import (
    export_gaokao_pathway_report,
    export_recommendation_summary,
    export_shandong_recommendation_report,
    export_volunteer_draft_summary,
)
from app.exporters.reports import (
    export_adviser_weekly_summary_report,
    export_adviser_quant_summary_report,
    export_class_analysis_report,
    export_evaluation_summary_report,
    export_grade_summary_report,
    export_planning_followup_report,
    export_student_analysis_report,
    export_student_followup_package,
    export_teacher_analysis_report,
)
from app.exporters.workload import export_workload_results
from app.models import RecommendationScheme, ReportExportRecord, Student
from app.repositories.exams import get_exam
from app.repositories.recommendations import get_employment_direction
from app.repositories.students import get_student_career_preference as repo_get_student_career_preference
from app.repositories.system import get_report_export, list_report_exports as repo_list_report_exports, write_audit_log
from app.schemas.recommendation import RecommendationHistoryItem
from app.schemas.report import (
    GaokaoPathwayReportExportPayload,
    PlanningFollowupReportExportPayload,
    ReportExportPayload,
    ReportExportRecordRead,
    ShandongRecommendationReportExportPayload,
)
from app.services import analytics as analytics_service
from app.services import archive as archive_service
from app.services import evaluation as evaluation_service
from app.services import planning as planning_service
from app.services import recommendations as recommendation_service
from app.services import student_events as student_event_service
from app.services import workload as workload_service


REPORT_TYPE_NAME_MAP = {
    "student_analysis": "学生成绩分析单",
    "class_analysis": "班级成绩分析报表",
    "grade_summary": "年级成绩汇总表",
    "teacher_analysis": "教师任教分析报表",
    "teacher_workload": "教师课时与工作量报表",
    "growth_summary": "学生成长档案摘要",
    "recommendation_summary": "学生推荐报告",
    "volunteer_draft_summary": "学生志愿草稿",
    "evaluation_summary": "评教汇总报表",
    "adviser_quant_summary": "班主任量化报表",
    "adviser_weekly_summary": "班主任周报",
    "student_followup_package": "学生跟进包",
    "planning_followup": "学生升学规划跟进表",
    "shandong_recommendation_summary": "山东普通类冲稳保推荐报告",
    "gaokao_pathway_report": "山东升学路径规划报告",
}


def _serialize_export_record(item: ReportExportRecord) -> ReportExportRecordRead:
    return ReportExportRecordRead(
        id=item.id,
        report_type=item.report_type,
        report_name=item.report_name,
        params_json=item.params_json,
        file_path=item.file_path,
        exported_at=item.exported_at,
        status=item.status,
        download_url=f"/api/reports/exports/{item.id}/download",
    )


def list_report_exports(session: Session) -> list[ReportExportRecordRead]:
    return [_serialize_export_record(item) for item in repo_list_report_exports(session)]


def get_report_export_record(session: Session, export_id: int) -> ReportExportRecord:
    item = get_report_export(session, export_id)
    if not item:
        raise HTTPException(status_code=404, detail="报表导出记录不存在")
    return item


def export_shandong_recommendation_report_record(
    session: Session,
    settings,
    payload: ShandongRecommendationReportExportPayload,
) -> ReportExportRecordRead:
    result = payload.result.model_dump(mode="json")
    file_path = export_shandong_recommendation_report(settings, result)
    record = ReportExportRecord(
        report_type="shandong_recommendation_summary",
        report_name=payload.report_name or REPORT_TYPE_NAME_MAP["shandong_recommendation_summary"],
        params_json={
            "report_type": "shandong_recommendation_summary",
            "student_id": result.get("student_id"),
            "student_name": result.get("student_name"),
            "target_year": result.get("target_year"),
            "source_mode": result.get("source_mode"),
            "predicted_rank": result.get("predicted_rank"),
        },
        file_path=file_path,
        status="success",
    )
    session.add(record)
    session.flush()
    write_audit_log(
        session,
        module="reports",
        action="export",
        target_type="report",
        target_id=str(record.id),
        detail_json={"report_type": "shandong_recommendation_summary", "file_path": file_path},
    )
    return _serialize_export_record(record)


def export_gaokao_pathway_report_record(
    session: Session,
    settings,
    payload: GaokaoPathwayReportExportPayload,
) -> ReportExportRecordRead:
    report = payload.report
    file_path = export_gaokao_pathway_report(settings, report)
    record = ReportExportRecord(
        report_type="gaokao_pathway_report",
        report_name=payload.report_name or REPORT_TYPE_NAME_MAP["gaokao_pathway_report"],
        params_json={
            "report_type": "gaokao_pathway_report",
            "student_id": report.get("student_id"),
            "student_name": report.get("student_name"),
            "target_year": report.get("target_year"),
            "pathway_count": len(report.get("cards") or []),
        },
        file_path=file_path,
        status="success",
    )
    session.add(record)
    session.flush()
    write_audit_log(
        session,
        module="reports",
        action="export",
        target_type="report",
        target_id=str(record.id),
        detail_json={"report_type": "gaokao_pathway_report", "file_path": file_path},
    )
    return _serialize_export_record(record)


def export_planning_followup_report_record(
    session: Session,
    settings,
    payload: PlanningFollowupReportExportPayload,
) -> ReportExportRecordRead:
    data = planning_service.build_planning_followup_export_payload(session, payload.student_id, exam_id=payload.exam_id)
    file_path = export_planning_followup_report(settings, data)
    student = data.get("student") if isinstance(data.get("student"), dict) else {}
    record = ReportExportRecord(
        report_type="planning_followup",
        report_name=payload.report_name or REPORT_TYPE_NAME_MAP["planning_followup"],
        params_json={
            "report_type": "planning_followup",
            "student_id": payload.student_id,
            "student_name": student.get("name"),
            "exam_id": payload.exam_id,
        },
        file_path=file_path,
        status="success",
    )
    session.add(record)
    session.flush()
    write_audit_log(
        session,
        module="reports",
        action="export",
        target_type="report",
        target_id=str(record.id),
        detail_json={"report_type": "planning_followup", "file_path": file_path},
    )
    return _serialize_export_record(record)


def export_report(session: Session, settings, payload: ReportExportPayload) -> ReportExportRecordRead:
    if payload.report_type not in REPORT_TYPE_NAME_MAP:
        raise HTTPException(status_code=400, detail="不支持的报表类型")

    report_name = REPORT_TYPE_NAME_MAP[payload.report_type]
    file_path = _export_report_file(session, settings, payload)
    record = ReportExportRecord(
        report_type=payload.report_type,
        report_name=report_name,
        params_json=payload.model_dump(mode="json", exclude_none=True),
        file_path=file_path,
        status="success",
    )
    session.add(record)
    session.flush()
    write_audit_log(
        session,
        module="reports",
        action="export",
        target_type="report",
        target_id=str(record.id),
        detail_json={"report_type": payload.report_type, "file_path": file_path},
    )
    return _serialize_export_record(record)


def _export_report_file(session: Session, settings, payload: ReportExportPayload) -> str:
    if payload.report_type == "student_analysis":
        if not payload.exam_id or not payload.student_id:
            raise HTTPException(status_code=400, detail="学生成绩分析单需要考试和学生参数")
        data = analytics_service.get_student_analytics(session, payload.student_id, payload.exam_id)
        return export_student_analysis_report(settings, data.model_dump(mode="json"))

    if payload.report_type == "class_analysis":
        if not payload.exam_id or not payload.class_id:
            raise HTTPException(status_code=400, detail="班级分析报表需要考试和班级参数")
        data = analytics_service.get_class_analytics(session, payload.class_id, payload.exam_id)
        return export_class_analysis_report(settings, data.model_dump(mode="json"))

    if payload.report_type == "grade_summary":
        if not payload.exam_id or not payload.grade_id:
            raise HTTPException(status_code=400, detail="年级汇总报表需要考试和年级参数")
        return _export_grade_summary(session, settings, payload.exam_id, payload.grade_id)

    if payload.report_type == "teacher_analysis":
        if not payload.exam_id or not payload.teacher_id:
            raise HTTPException(status_code=400, detail="教师任教分析报表需要考试和教师参数")
        data = analytics_service.get_teacher_analytics(session, payload.teacher_id, payload.exam_id)
        return export_teacher_analysis_report(settings, data.model_dump(mode="json"))

    if payload.report_type == "teacher_workload":
        if not payload.semester_id:
            raise HTTPException(status_code=400, detail="教师工作量报表需要学期参数")
        rows = [
            item.model_dump(mode="json")
            for item in workload_service.list_workload_results(
                session,
                semester_id=payload.semester_id,
                rule_version_id=payload.rule_version_id,
            )
        ]
        if not rows:
            raise HTTPException(status_code=404, detail="当前条件下暂无工作量结果")
        return export_workload_results(settings, rows)

    if payload.report_type == "growth_summary":
        if not payload.student_id:
            raise HTTPException(status_code=400, detail="成长档案摘要需要学生参数")
        student = session.get(Student, payload.student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")
        timeline = archive_service.list_growth_records(session, payload.student_id)
        if timeline.total == 0:
            raise HTTPException(status_code=404, detail="该学生暂无成长记录")
        return export_growth_summary(
            settings,
            {
                "student_no": student.student_no,
                "student_name": student.name,
                "grade_name": student.current_grade.name if student.current_grade else None,
                "class_name": student.current_class.name if student.current_class else None,
            },
            [item.model_dump(mode="json") for item in timeline.items],
        )

    if payload.report_type == "recommendation_summary":
        if not payload.scheme_id:
            raise HTTPException(status_code=400, detail="学生推荐报告需要方案参数")
        rows = recommendation_service.list_scheme_results(session, payload.scheme_id, student_id=payload.student_id)
        if not rows:
            raise HTTPException(status_code=404, detail="当前推荐方案暂无结果")
        first = rows[0]
        export_student_id = payload.student_id or first.student_id
        exam = get_exam(session, first.exam_id)
        scheme = session.get(RecommendationScheme, payload.scheme_id)
        preference = repo_get_student_career_preference(session, export_student_id) if export_student_id else None
        snapshot = first.snapshot_json if isinstance(first.snapshot_json, dict) else {}
        compare_scheme = None
        compare_rows: list[dict[str, object]] = []
        if export_student_id:
            history = recommendation_service.list_recommendation_history(session, student_id=export_student_id)
            current_history = next((item for item in history if item.scheme_id == payload.scheme_id), None)
            compare_history = _find_nearest_recommendation_compare_scheme(history, current_history)
            if compare_history:
                compare_scheme = {
                    "scheme_id": compare_history.scheme_id,
                    "scheme_name": compare_history.scheme_name,
                    "generated_at": compare_history.generated_at,
                    "province": compare_history.province,
                    "target_year": compare_history.target_year,
                }
                compare_rows = [
                    item.model_dump(mode="json")
                    for item in recommendation_service.list_scheme_results(
                        session,
                        compare_history.scheme_id,
                        student_id=export_student_id,
                    )
                ]
        return export_recommendation_summary(
            settings,
            {
                "scheme_name": first.scheme_name,
                "student_name": first.student_name,
                "exam_name": exam.name if exam else first.exam_id,
                "province": scheme.province if scheme else first.snapshot_json.get("province") if first.snapshot_json else None,
                "target_year": scheme.target_year if scheme else snapshot.get("target_year"),
                "score_input_label": snapshot.get("score_input_label")
                or _score_input_mode_label(snapshot.get("score_input_mode")),
                "simulation_note": _build_simulation_note(
                    score_confidence=snapshot.get("score_confidence"),
                    reference_exam_name=snapshot.get("reference_exam_name"),
                    use_historical_mapping=snapshot.get("use_historical_mapping"),
                ),
                "target_direction_summary": _build_preference_direction_summary(
                    session,
                    preference.primary_direction_id if preference else None,
                    preference.primary_direction.name if preference and preference.primary_direction else None,
                    preference.secondary_direction_id if preference else None,
                    preference.secondary_direction.name if preference and preference.secondary_direction else None,
                    preference.alternative_direction_id if preference else None,
                    preference.alternative_direction.name if preference and preference.alternative_direction else None,
                )
                or _build_result_direction_summary([item.model_dump(mode="json") for item in rows]),
                "accepted_path_summary": _build_accepted_path_summary(
                    accepts_postgraduate=preference.accepts_postgraduate if preference else False,
                    accepts_public_service=preference.accepts_public_service if preference else False,
                    accepts_certificate=preference.accepts_certificate if preference else False,
                    accepts_long_training=preference.accepts_long_training if preference else False,
                ),
                "compare_scheme": compare_scheme,
                "compare_rows": compare_rows,
            },
            [item.model_dump(mode="json") for item in rows],
        )

    if payload.report_type == "volunteer_draft_summary":
        if not payload.draft_id:
            raise HTTPException(status_code=400, detail="学生志愿草稿需要草稿参数")
        draft = recommendation_service.get_volunteer_draft_detail(session, payload.draft_id)
        if not draft.items:
            raise HTTPException(status_code=404, detail="当前志愿草稿暂无内容")
        selected_rule = draft.selected_rule
        rule_label = None
        if selected_rule:
            rule_label = f"{selected_rule.batch} / {selected_rule.exam_mode} / {selected_rule.volunteer_unit_type} / 上限 {selected_rule.volunteer_limit}"
        return export_volunteer_draft_summary(
            settings,
            {
                "draft_name": draft.name,
                "student_name": draft.student_name,
                "exam_name": draft.exam_name,
                "province": draft.province,
                "target_year": draft.target_year,
                "batch": draft.batch,
                "exam_mode": draft.exam_mode,
                "score_input_label": _score_input_mode_label(draft.score_input_mode),
                "simulation_note": _build_simulation_note(
                    score_confidence=_score_confidence_by_mode(draft.score_input_mode),
                    reference_exam_name=draft.reference_exam_name,
                    use_historical_mapping=draft.use_historical_mapping,
                ),
                "target_direction_summary": _build_preference_direction_summary(
                    session,
                    draft.primary_direction_id,
                    None,
                    draft.secondary_direction_id,
                    None,
                    draft.alternative_direction_id,
                    None,
                )
                or _build_result_direction_summary(
                    [
                        {
                            "matched_direction_names_json": item.candidate.matched_direction_names_json,
                        }
                        for item in draft.items
                    ]
                ),
                "accepted_path_summary": _build_accepted_path_summary(
                    accepts_postgraduate=draft.accepts_postgraduate,
                    accepts_public_service=draft.accepts_public_service,
                    accepts_certificate=draft.accepts_certificate,
                    accepts_long_training=draft.accepts_long_training,
                ),
                "rule_label": rule_label,
                "rule_alerts": [item.model_dump(mode="json") for item in draft.rule_alerts],
                "note": draft.note,
            },
            [
                {
                    "order": item.order,
                    **item.candidate.model_dump(mode="json"),
                }
                for item in draft.items
            ],
        )

    if payload.report_type == "evaluation_summary":
        if not payload.batch_id:
            raise HTTPException(status_code=400, detail="评教汇总报表需要评教批次参数")
        overview = evaluation_service.get_evaluation_batch_overview(session, payload.batch_id)
        detail_rows: list[dict[str, object]] = []
        for teacher in overview.teacher_summaries:
            detail = evaluation_service.get_evaluation_teacher_detail(session, payload.batch_id, teacher.teacher_id)
            for dimension in detail.dimension_summaries:
                detail_rows.append(
                    {
                        "teacher_name": teacher.teacher_name,
                        "dimension_name": dimension.dimension_name,
                        "avg_score": dimension.avg_score,
                        "response_count": dimension.response_count,
                    }
                )
        return export_evaluation_summary_report(
            settings,
            {
                "template_name": overview.template_name,
                "semester_name": overview.semester_name,
            },
            [item.model_dump(mode="json") for item in overview.teacher_summaries],
            detail_rows,
        )

    if payload.report_type == "adviser_quant_summary":
        if not payload.semester_id:
            raise HTTPException(status_code=400, detail="班主任量化报表需要学期参数")
        summary_rows = evaluation_service.list_adviser_summary(
            session,
            semester_id=payload.semester_id,
            rule_version_id=payload.rule_version_id,
            teacher_id=payload.teacher_id,
        )
        if not summary_rows:
            raise HTTPException(status_code=404, detail="当前条件下暂无班主任量化结果")
        detail_rows = evaluation_service.list_adviser_records(
            session,
            semester_id=payload.semester_id,
            teacher_id=payload.teacher_id,
        )
        if payload.rule_version_id:
            detail_rows = [item for item in detail_rows if item.rule_version_id == payload.rule_version_id]
        return export_adviser_quant_summary_report(
            settings,
            {
                "semester_name": summary_rows[0].semester_name,
                "rule_version_name": summary_rows[0].rule_version_name,
            },
            [item.model_dump(mode="json") for item in summary_rows],
            [item.model_dump(mode="json") for item in detail_rows],
        )

    if payload.report_type == "adviser_weekly_summary":
        dashboard = student_event_service.get_adviser_dashboard(
            session,
            grade_id=payload.grade_id,
            class_id=payload.class_id,
            exam_id=payload.exam_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        data = dashboard.model_dump(mode="json")
        data["generated_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
        return export_adviser_weekly_summary_report(settings, data)

    if payload.report_type == "student_followup_package":
        if not payload.student_id:
            raise HTTPException(status_code=400, detail="学生跟进包需要学生参数")
        summary = student_event_service.get_student_risk(
            session,
            payload.student_id,
            exam_id=payload.exam_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        data = summary.model_dump(mode="json")
        data["generated_at"] = datetime.now().isoformat(sep=" ", timespec="seconds")
        return export_student_followup_package(settings, data)

    if payload.report_type == "planning_followup":
        if not payload.student_id:
            raise HTTPException(status_code=400, detail="学生升学规划跟进表需要学生参数")
        data = planning_service.build_planning_followup_export_payload(
            session,
            payload.student_id,
            exam_id=payload.exam_id,
        )
        return export_planning_followup_report(settings, data)

    raise HTTPException(status_code=400, detail="不支持的报表类型")


def _build_preference_direction_summary(
    session: Session,
    primary_direction_id: int | None,
    primary_direction_name: str | None,
    secondary_direction_id: int | None,
    secondary_direction_name: str | None,
    alternative_direction_id: int | None,
    alternative_direction_name: str | None,
) -> str | None:
    segments: list[str] = []
    for label, direction_id, direction_name in [
        ("首选", primary_direction_id, primary_direction_name),
        ("次选", secondary_direction_id, secondary_direction_name),
        ("替代", alternative_direction_id, alternative_direction_name),
    ]:
        if direction_id is None:
            continue
        current_name = direction_name
        if not current_name:
            direction = get_employment_direction(session, direction_id)
            current_name = direction.name if direction and direction.is_active else f"方向 {direction_id}"
        segments.append(f"{label}：{current_name}")
    return " / ".join(segments) or None


def _find_nearest_recommendation_compare_scheme(
    history: list[RecommendationHistoryItem],
    current: RecommendationHistoryItem | None,
) -> RecommendationHistoryItem | None:
    if not current:
        return None

    return min(
        (
            item
            for item in history
            if item.student_id == current.student_id and item.scheme_id != current.scheme_id
        ),
        key=lambda item: (
            _get_generated_at_distance(item.generated_at, current.generated_at),
            -item.generated_at.timestamp(),
        ),
        default=None,
    )


def _get_generated_at_distance(value: datetime, target: datetime) -> float:
    return abs((value - target).total_seconds())


def _build_result_direction_summary(rows: list[dict[str, object]]) -> str | None:
    direction_names: list[str] = []
    for row in rows:
        current = row.get("matched_direction_names_json")
        if not isinstance(current, list):
            continue
        for item in current:
            if isinstance(item, str) and item.strip() and item.strip() not in direction_names:
                direction_names.append(item.strip())
    return " / ".join(direction_names) or None


def _build_accepted_path_summary(
    *,
    accepts_postgraduate: bool,
    accepts_public_service: bool,
    accepts_certificate: bool,
    accepts_long_training: bool,
) -> str | None:
    accepted: list[str] = []
    if accepts_postgraduate:
        accepted.append("接受读研路径")
    if accepts_public_service:
        accepted.append("接受考公/考编路径")
    if accepts_certificate:
        accepted.append("接受资格证路径")
    if accepts_long_training:
        accepted.append("接受长培养周期")
    return " / ".join(accepted) or None


def _score_input_mode_label(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    labels = {
        "actual_rank": "正式位次",
        "actual_score": "正式分数",
        "estimated_score": "预估分数",
        "estimated_score_and_rank": "预估分数 + 预估位次",
        "score_range": "分数区间",
        "rank_range": "位次区间",
    }
    current = value.strip()
    return labels.get(current, current or None)


def _score_confidence_by_mode(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    mapping = {
        "actual_rank": "official",
        "actual_score": "score_only",
        "estimated_score": "estimated",
        "estimated_score_and_rank": "estimated",
        "score_range": "range_estimated",
        "rank_range": "range_estimated",
    }
    return mapping.get(value.strip())


def _build_simulation_note(
    *,
    score_confidence: object,
    reference_exam_name: object,
    use_historical_mapping: object,
) -> str | None:
    segments: list[str] = []
    if isinstance(score_confidence, str) and score_confidence in {"estimated", "range_estimated", "score_only"}:
        confidence_labels = {
            "estimated": "当前结果为模拟测算",
            "range_estimated": "当前结果为区间模拟测算",
            "score_only": "当前结果按分数模式测算",
        }
        label = confidence_labels.get(score_confidence)
        if label:
            segments.append(label)
    if isinstance(reference_exam_name, str) and reference_exam_name.strip():
        segments.append(f"参考考试：{reference_exam_name.strip()}")
    if use_historical_mapping is True:
        segments.append("已启用历史映射")
    return " / ".join(segments) or None


def _export_grade_summary(session: Session, settings, exam_id: int, grade_id: int) -> str:
    analytics = analytics_service.get_grade_analytics(session, grade_id, exam_id)
    return export_grade_summary_report(
        settings,
        {
            "exam_name": analytics.exam_name,
            "grade_name": analytics.grade_name,
            "student_count": analytics.student_count,
            "total_average": analytics.total_average,
            "total_median": analytics.total_median,
            "excellent_rate": analytics.excellent_rate,
        },
        [item.model_dump(mode="json") for item in analytics.class_breakdown],
        [item.model_dump(mode="json") for item in analytics.subject_breakdown],
        f"{analytics.exam_name} 年级汇总",
    )
