from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.analytics.scores import calculate_rate, safe_mean, safe_median
from app.exporters.archive import export_growth_summary
from app.exporters.recommendations import export_recommendation_summary
from app.exporters.reports import (
    export_adviser_quant_summary_report,
    export_class_analysis_report,
    export_evaluation_summary_report,
    export_grade_summary_report,
    export_student_analysis_report,
    export_teacher_analysis_report,
)
from app.exporters.workload import export_workload_results
from app.models import RecommendationScheme, ReportExportRecord, Student, Subject
from app.repositories.exams import get_exam, get_subject_snapshots_for_exam, get_total_snapshots_for_exam
from app.repositories.system import get_report_export, list_report_exports as repo_list_report_exports, write_audit_log
from app.schemas.report import ReportExportPayload, ReportExportRecordRead
from app.services import analytics as analytics_service
from app.services import archive as archive_service
from app.services import evaluation as evaluation_service
from app.services import recommendations as recommendation_service
from app.services import workload as workload_service


REPORT_TYPE_NAME_MAP = {
    "student_analysis": "学生成绩分析单",
    "class_analysis": "班级成绩分析报表",
    "grade_summary": "年级成绩汇总表",
    "teacher_analysis": "教师任教分析报表",
    "teacher_workload": "教师课时与工作量报表",
    "growth_summary": "学生成长档案摘要",
    "recommendation_summary": "学生推荐报告",
    "evaluation_summary": "评教汇总报表",
    "adviser_quant_summary": "班主任量化报表",
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


def export_report(session: Session, settings, payload: ReportExportPayload) -> ReportExportRecordRead:
    if payload.report_type not in REPORT_TYPE_NAME_MAP:
        raise HTTPException(status_code=400, detail="不支持的报表类型")

    report_name = REPORT_TYPE_NAME_MAP[payload.report_type]
    file_path = _export_report_file(session, settings, payload)
    record = ReportExportRecord(
        report_type=payload.report_type,
        report_name=report_name,
        params_json=payload.model_dump(exclude_none=True),
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
        exam = get_exam(session, first.exam_id)
        scheme = session.get(RecommendationScheme, payload.scheme_id)
        return export_recommendation_summary(
            settings,
            {
                "scheme_name": first.scheme_name,
                "student_name": first.student_name,
                "exam_name": exam.name if exam else first.exam_id,
                "province": scheme.province if scheme else first.snapshot_json.get("province") if first.snapshot_json else None,
            },
            [item.model_dump(mode="json") for item in rows],
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

    raise HTTPException(status_code=400, detail="不支持的报表类型")


def _export_grade_summary(session: Session, settings, exam_id: int, grade_id: int) -> str:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    total_snapshots = [
        item
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_grade_id == grade_id
    ]
    if not total_snapshots:
        raise HTTPException(status_code=404, detail="该年级暂无总分数据")

    class_group: dict[int, list] = defaultdict(list)
    for item in total_snapshots:
        if item.student and item.student.current_class_id:
            class_group[item.student.current_class_id].append(item)

    summary_rows: list[dict[str, object]] = []
    for items in class_group.values():
        scores = [item.total_score for item in items]
        summary_rows.append(
            {
                "class_name": items[0].student.current_class.name if items[0].student and items[0].student.current_class else "未分班",
                "student_count": len(items),
                "average_score": safe_mean(scores),
                "median_score": safe_median(scores),
                "max_score": max(scores),
                "min_score": min(scores),
            }
        )
    summary_rows.sort(key=lambda item: item["class_name"] or "")

    subject_snapshots = [
        item
        for item in get_subject_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_grade_id == grade_id and item.score is not None
    ]
    subject_map = {subject.id: subject.name for subject in session.query(Subject).all()}
    grouped_subjects: dict[int, list] = defaultdict(list)
    for item in subject_snapshots:
        grouped_subjects[item.subject_id].append(item)
    subject_rows = []
    for subject_id, items in grouped_subjects.items():
        scores = [item.score for item in items if item.score is not None]
        subject_rows.append(
            {
                "subject_name": subject_map.get(subject_id, str(subject_id)),
                "valid_count": len(scores),
                "average_score": safe_mean(scores),
                "excellent_rate": calculate_rate(sum(1 for item in items if item.excellent_flag), len(scores)),
                "pass_rate": calculate_rate(sum(1 for item in items if item.pass_flag), len(scores)),
            }
        )
    subject_rows.sort(key=lambda item: item["subject_name"])
    return export_grade_summary_report(settings, summary_rows, subject_rows, f"{exam.name} 年级汇总")
