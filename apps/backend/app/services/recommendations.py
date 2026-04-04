from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.recommendations import classify_ratio, classify_score_gap, weighted_reference_rank
from app.core.config import Settings
from app.importers.admissions import AdmissionImporter
from app.models import (
    AdmissionRecord,
    College,
    CollegeAlias,
    ConfigItem,
    Major,
    RecommendationResult,
    RecommendationScheme,
    Student,
)
from app.repositories.exams import get_exam, get_total_snapshots_for_exam
from app.repositories.recommendations import (
    get_college,
    get_college_by_name,
    get_major,
    get_major_by_name,
    get_scheme,
    list_admission_candidates,
    list_admission_records as repo_list_admission_records,
    list_colleges as repo_list_colleges,
    list_majors as repo_list_majors,
    list_recommendation_results,
)
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.recommendation import (
    AdmissionImportResponse,
    AdmissionRecordRead,
    CollegePayload,
    CollegeRead,
    MajorPayload,
    MajorRead,
    RecommendationBatchGeneratePayload,
    RecommendationGeneratePayload,
    RecommendationGenerateResponse,
    RecommendationHistoryItem,
    RecommendationResultRead,
    RecommendationSettingsPayload,
    RecommendationSettingsRead,
    RecommendationCollegeOption,
    RecommendationStrategyPresetPayload,
    RecommendationStrategyPresetRead,
)


RECOMMENDATION_CONFIG_DEFAULTS = {
    "safe_ratio_max": ("0.85", "float", "保底区间上限"),
    "steady_ratio_max": ("1.00", "float", "稳妥区间上限"),
    "rush_ratio_max": ("1.15", "float", "冲刺区间上限"),
    "whitelist_college_ids_json": ("[]", "json", "推荐白名单院校"),
    "blacklist_college_ids_json": ("[]", "json", "推荐黑名单院校"),
    "strategy_presets_json": ("[]", "json", "推荐策略模板"),
}


class RecommendationSettingsState:
    def __init__(
        self,
        *,
        safe_ratio_max: float,
        steady_ratio_max: float,
        rush_ratio_max: float,
        whitelist_college_ids: list[int],
        blacklist_college_ids: list[int],
    ) -> None:
        self.safe_ratio_max = safe_ratio_max
        self.steady_ratio_max = steady_ratio_max
        self.rush_ratio_max = rush_ratio_max
        self.whitelist_college_ids = whitelist_college_ids
        self.blacklist_college_ids = blacklist_college_ids


def _serialize_college(item: College) -> CollegeRead:
    return CollegeRead(
        id=item.id,
        name=item.name,
        college_code=item.college_code,
        province=item.province,
        city=item.city,
        school_type=item.school_type,
        school_level_tags_json=item.school_level_tags_json,
        intro=item.intro,
        website=item.website,
        supports_art=item.supports_art,
        note=item.note,
        alias_names=[alias.alias_name for alias in item.aliases if alias.is_active],
        is_active=item.is_active,
    )


def _serialize_major(item: Major) -> MajorRead:
    return MajorRead.model_validate(item)


def _serialize_admission_record(item: AdmissionRecord) -> AdmissionRecordRead:
    return AdmissionRecordRead(
        id=item.id,
        year=item.year,
        province=item.province,
        batch=item.batch,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        major_id=item.major_id,
        major_name=item.major.name if item.major else None,
        student_type=item.student_type,
        art_track=item.art_track,
        subject_requirement=item.subject_requirement,
        min_score=item.min_score,
        min_rank=item.min_rank,
        avg_score=item.avg_score,
        max_score=item.max_score,
        plan_count=item.plan_count,
        source_note=item.source_note,
        is_active=item.is_active,
    )


def _serialize_result(item: RecommendationResult) -> RecommendationResultRead:
    return RecommendationResultRead(
        id=item.id,
        student_id=item.student_id,
        student_name=item.student.name if item.student else None,
        exam_id=item.exam_id,
        scheme_id=item.scheme_id,
        scheme_name=item.scheme.name if item.scheme else None,
        result_type=item.result_type,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        major_id=item.major_id,
        major_name=item.major.name if item.major else None,
        reference_rank=item.reference_rank,
        student_rank=item.student_rank,
        score_basis=item.score_basis,
        ratio=item.ratio,
        reason_text=item.reason_text,
        risk_flags_json=item.risk_flags_json,
        snapshot_json=item.snapshot_json,
        generated_at=item.generated_at,
        is_active=item.is_active,
    )


def list_colleges(
    session: Session,
    *,
    keyword: str | None = None,
    province: str | None = None,
    supports_art: bool | None = None,
) -> list[CollegeRead]:
    return [
        _serialize_college(item)
        for item in repo_list_colleges(session, keyword=keyword, province=province, supports_art=supports_art)
    ]


def create_college(session: Session, payload: CollegePayload) -> CollegeRead:
    existing = get_college_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="院校名称已存在")
    item = College(name=payload.name.strip())
    session.add(item)
    session.flush()
    _apply_college_payload(item, payload)
    write_audit_log(session, module="recommendations", action="create_college", target_type="college", target_id=str(item.id))
    session.refresh(item)
    return _serialize_college(item)


def update_college(session: Session, college_id: int, payload: CollegePayload) -> CollegeRead:
    item = get_college(session, college_id)
    if not item:
        raise HTTPException(status_code=404, detail="院校不存在")
    existing = get_college_by_name(session, payload.name)
    if existing and existing.id != college_id:
        raise HTTPException(status_code=400, detail="院校名称已存在")
    _apply_college_payload(item, payload)
    write_audit_log(session, module="recommendations", action="update_college", target_type="college", target_id=str(item.id))
    session.refresh(item)
    return _serialize_college(item)


def _apply_college_payload(item: College, payload: CollegePayload) -> None:
    item.name = payload.name.strip()
    item.college_code = payload.college_code
    item.province = payload.province
    item.city = payload.city
    item.school_type = payload.school_type
    item.school_level_tags_json = payload.school_level_tags_json or None
    item.intro = payload.intro
    item.website = payload.website
    item.supports_art = payload.supports_art
    item.note = payload.note
    item.is_active = payload.is_active
    item.aliases.clear()
    for alias_name in payload.alias_names:
        cleaned = alias_name.strip()
        if cleaned:
            item.aliases.append(CollegeAlias(alias_name=cleaned))


def list_majors(session: Session, *, keyword: str | None = None, is_art_related: bool | None = None) -> list[MajorRead]:
    return [_serialize_major(item) for item in repo_list_majors(session, keyword=keyword, is_art_related=is_art_related)]


def create_major(session: Session, payload: MajorPayload) -> MajorRead:
    existing = get_major_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="专业名称已存在")
    item = Major(**payload.model_dump())
    session.add(item)
    session.flush()
    write_audit_log(session, module="recommendations", action="create_major", target_type="major", target_id=str(item.id))
    session.refresh(item)
    return _serialize_major(item)


def update_major(session: Session, major_id: int, payload: MajorPayload) -> MajorRead:
    item = get_major(session, major_id)
    if not item:
        raise HTTPException(status_code=404, detail="专业不存在")
    existing = get_major_by_name(session, payload.name)
    if existing and existing.id != major_id:
        raise HTTPException(status_code=400, detail="专业名称已存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.flush()
    write_audit_log(session, module="recommendations", action="update_major", target_type="major", target_id=str(item.id))
    session.refresh(item)
    return _serialize_major(item)


def list_admission_records(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    college_id: int | None = None,
) -> list[AdmissionRecordRead]:
    return [
        _serialize_admission_record(item)
        for item in repo_list_admission_records(session, year=year, province=province, college_id=college_id)
    ]


def import_admissions(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
) -> AdmissionImportResponse:
    job = create_import_job(session, "admissions", filename)
    job.started_at = datetime.now()
    importer = AdmissionImporter(session, settings)
    result, created_colleges, created_majors = importer.execute(filename=filename, content=content)
    job.finished_at = datetime.now()
    job.status = "success" if result.failed_rows == 0 else "partial_success"
    job.result_json = {
        **result.model_dump(),
        "created_college_count": created_colleges,
        "created_major_count": created_majors,
    }
    write_audit_log(
        session,
        module="recommendations",
        action="import_admissions",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=job.result_json,
    )
    return AdmissionImportResponse(
        created_college_count=created_colleges,
        created_major_count=created_majors,
        **result.model_dump(),
    )


def generate_recommendations(
    session: Session,
    payload: RecommendationGeneratePayload,
) -> RecommendationGenerateResponse:
    return _generate_for_student(session, payload)


def batch_generate_recommendations(
    session: Session,
    payload: RecommendationBatchGeneratePayload,
) -> dict[str, object]:
    if not payload.student_ids:
        raise HTTPException(status_code=400, detail="学生列表不能为空")
    scheme_ids: list[int] = []
    total_result_count = 0
    for student_id in payload.student_ids:
        result = _generate_for_student(
            session,
            RecommendationGeneratePayload(
                student_id=student_id,
                exam_id=payload.exam_id,
                name=payload.name,
                target_year=payload.target_year,
                province=payload.province,
                target_regions_json=payload.target_regions_json,
                school_level_tags_json=payload.school_level_tags_json,
                major_keyword=payload.major_keyword,
                subject_combination=payload.subject_combination,
                obey_adjustment=payload.obey_adjustment,
                note=payload.note,
            ),
        )
        scheme_ids.append(result.scheme_id)
        total_result_count += result.result_count
    return {
        "message": "批量推荐完成",
        "scheme_ids": scheme_ids,
        "result_count": total_result_count,
    }


def list_recommendation_history(session: Session, student_id: int | None = None) -> list[RecommendationHistoryItem]:
    rows = list_recommendation_results(session, student_id=student_id)
    grouped: dict[tuple[int, int], list[RecommendationResult]] = defaultdict(list)
    for row in rows:
        grouped[(row.scheme_id, row.student_id)].append(row)

    history: list[RecommendationHistoryItem] = []
    for items in grouped.values():
        first = items[0]
        counts = defaultdict(int)
        for item in items:
            counts[item.result_type] += 1
        history.append(
            RecommendationHistoryItem(
                scheme_id=first.scheme_id,
                scheme_name=first.scheme.name if first.scheme else str(first.scheme_id),
                student_id=first.student_id,
                student_name=first.student.name if first.student else str(first.student_id),
                exam_id=first.exam_id,
                province=first.scheme.province if first.scheme else "",
                student_type=first.scheme.student_type if first.scheme else "",
                generated_at=max(item.generated_at for item in items),
                result_count=len(items),
                challenge_count=counts["challenge"],
                steady_count=counts["steady"],
                safe_count=counts["safe"],
            )
        )
    history.sort(key=lambda item: item.generated_at, reverse=True)
    return history


def list_scheme_results(session: Session, scheme_id: int, student_id: int | None = None) -> list[RecommendationResultRead]:
    scheme = get_scheme(session, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="推荐方案不存在")
    return [_serialize_result(item) for item in list_recommendation_results(session, student_id=student_id, scheme_id=scheme_id)]


def get_recommendation_settings(session: Session) -> RecommendationSettingsRead:
    state = _load_recommendation_settings_state(session)
    return _serialize_recommendation_settings(session, state)


def update_recommendation_settings(
    session: Session,
    payload: RecommendationSettingsPayload,
) -> RecommendationSettingsRead:
    _validate_strategy_values(
        safe_ratio_max=payload.safe_ratio_max,
        steady_ratio_max=payload.steady_ratio_max,
        rush_ratio_max=payload.rush_ratio_max,
        whitelist_college_ids=payload.whitelist_college_ids,
        blacklist_college_ids=payload.blacklist_college_ids,
    )
    values = {
        "safe_ratio_max": str(payload.safe_ratio_max),
        "steady_ratio_max": str(payload.steady_ratio_max),
        "rush_ratio_max": str(payload.rush_ratio_max),
        "whitelist_college_ids_json": json.dumps(sorted(set(payload.whitelist_college_ids)), ensure_ascii=False),
        "blacklist_college_ids_json": json.dumps(sorted(set(payload.blacklist_college_ids)), ensure_ascii=False),
    }
    _upsert_recommendation_config_values(session, values)
    write_audit_log(
        session,
        module="recommendations",
        action="update_settings",
        target_type="config_group",
        target_id="recommendation",
        detail_json=payload.model_dump(),
    )
    return get_recommendation_settings(session)


def create_recommendation_strategy_preset(
    session: Session,
    payload: RecommendationStrategyPresetPayload,
) -> RecommendationSettingsRead:
    _validate_strategy_values(
        safe_ratio_max=payload.safe_ratio_max,
        steady_ratio_max=payload.steady_ratio_max,
        rush_ratio_max=payload.rush_ratio_max,
        whitelist_college_ids=payload.whitelist_college_ids,
        blacklist_college_ids=payload.blacklist_college_ids,
    )
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="模板名称不能为空")

    presets = _load_strategy_preset_payloads(session)
    preset = {
        "id": uuid4().hex,
        "name": payload.name.strip(),
        "note": payload.note.strip() if payload.note else None,
        "safe_ratio_max": payload.safe_ratio_max,
        "steady_ratio_max": payload.steady_ratio_max,
        "rush_ratio_max": payload.rush_ratio_max,
        "whitelist_college_ids": sorted(set(payload.whitelist_college_ids)),
        "blacklist_college_ids": sorted(set(payload.blacklist_college_ids)),
        "created_at": datetime.now().isoformat(),
    }
    presets.append(preset)
    _upsert_recommendation_config_values(
        session,
        {"strategy_presets_json": json.dumps(presets, ensure_ascii=False)},
    )
    write_audit_log(
        session,
        module="recommendations",
        action="create_strategy_preset",
        target_type="recommendation_strategy_preset",
        target_id=preset["id"],
        detail_json=preset,
    )
    return get_recommendation_settings(session)


def delete_recommendation_strategy_preset(session: Session, preset_id: str) -> RecommendationSettingsRead:
    presets = _load_strategy_preset_payloads(session)
    remaining = [item for item in presets if str(item.get("id")) != preset_id]
    if len(remaining) == len(presets):
        raise HTTPException(status_code=404, detail="推荐策略模板不存在")
    _upsert_recommendation_config_values(
        session,
        {"strategy_presets_json": json.dumps(remaining, ensure_ascii=False)},
    )
    write_audit_log(
        session,
        module="recommendations",
        action="delete_strategy_preset",
        target_type="recommendation_strategy_preset",
        target_id=preset_id,
    )
    return get_recommendation_settings(session)


def _generate_for_student(session: Session, payload: RecommendationGeneratePayload) -> RecommendationGenerateResponse:
    student = session.get(Student, payload.student_id)
    exam = get_exam(session, payload.exam_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    settings = _load_recommendation_settings_state(session)
    target_year = payload.target_year or exam.exam_date.year
    student_type = _detect_student_type(student)
    student_total_score, snapshot_rank = _get_student_exam_metrics(session, payload.student_id, payload.exam_id)
    student_rank = payload.student_rank_override or snapshot_rank
    candidate_records = _filter_candidates(
        session,
        province=payload.province,
        student=student,
        student_type=student_type,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
    )
    if not candidate_records:
        raise HTTPException(status_code=404, detail="当前条件下暂无可推荐的录取数据")

    scheme = RecommendationScheme(
        name=(payload.name or f"{student.name}-{exam.name}-推荐").strip(),
        target_year=target_year,
        province=payload.province,
        student_type=student_type,
        rule_json={
            "target_regions_json": payload.target_regions_json,
            "school_level_tags_json": payload.school_level_tags_json,
            "major_keyword": payload.major_keyword,
            "subject_combination": payload.subject_combination,
            "obey_adjustment": payload.obey_adjustment,
            "student_rank_override": payload.student_rank_override,
            "comprehensive_score": payload.comprehensive_score,
            "professional_score": payload.professional_score,
            "culture_score": payload.culture_score,
            "note": payload.note,
        },
        is_default=False,
    )
    session.add(scheme)
    session.flush()

    thresholds = {
        "safe": settings.safe_ratio_max,
        "steady": settings.steady_ratio_max,
        "rush": settings.rush_ratio_max,
    }
    grouped_candidates: dict[tuple[int, int | None], list[AdmissionRecord]] = defaultdict(list)
    for item in candidate_records:
        grouped_candidates[(item.college_id, item.major_id)].append(item)

    results: list[RecommendationResult] = []
    score_value = payload.comprehensive_score or payload.culture_score or student_total_score
    for (college_id, major_id), records in grouped_candidates.items():
        result = _build_recommendation_result(
            student=student,
            exam_id=payload.exam_id,
            scheme_id=scheme.id,
            student_type=student_type,
            student_rank=student_rank,
            score_value=score_value,
            records=records,
            thresholds=thresholds,
            is_whitelisted=college_id in set(settings.whitelist_college_ids),
        )
        if result:
            results.append(result)

    if not results:
        raise HTTPException(status_code=404, detail="当前条件下没有可生成的推荐结果")

    for item in results:
        session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="generate",
        target_type="recommendation_scheme",
        target_id=str(scheme.id),
        detail_json={"student_id": payload.student_id, "result_count": len(results)},
    )
    serialized = [_serialize_result(item) for item in list_recommendation_results(session, student_id=payload.student_id, scheme_id=scheme.id)]
    return RecommendationGenerateResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        student_id=payload.student_id,
        result_count=len(serialized),
        challenge=[item for item in serialized if item.result_type == "challenge"],
        steady=[item for item in serialized if item.result_type == "steady"],
        safe=[item for item in serialized if item.result_type == "safe"],
    )


def _build_recommendation_result(
    *,
    student: Student,
    exam_id: int,
    scheme_id: int,
    student_type: str,
    student_rank: int | None,
    score_value: float | None,
    records: list[AdmissionRecord],
    thresholds: dict[str, float],
    is_whitelisted: bool = False,
) -> RecommendationResult | None:
    first = sorted(records, key=lambda item: item.year, reverse=True)[0]
    rank_values = [(item.year, item.min_rank) for item in records if item.min_rank]
    reference_rank = weighted_reference_rank([(year, rank) for year, rank in rank_values if rank is not None])
    risk_flags: list[str] = []
    ratio = None
    result_type = None
    score_basis = "rank"

    if reference_rank and student_rank:
        ratio = round(student_rank / reference_rank, 4)
        result_type = classify_ratio(
            ratio,
            safe_max=thresholds["safe"],
            steady_max=thresholds["steady"],
            rush_max=thresholds["rush"],
        )
        if len(rank_values) < 2:
            risk_flags.append("sample_insufficient")
    elif first.min_score is not None and score_value is not None:
        result_type = classify_score_gap(round(score_value - first.min_score, 2))
        score_basis = "comprehensive_score" if student_type != "general" else "score"
        risk_flags.append("rank_missing")
    else:
        return None

    if not result_type:
        return None
    if student_type != "general":
        risk_flags.append("art_recommendation")
        if first.art_track is None:
            risk_flags.append("track_unconfirmed")
        if score_basis != "rank":
            risk_flags.append("manual_formula_check")
    if is_whitelisted:
        risk_flags.append("whitelist_override")

    reference_years = sorted({item.year for item in records}, reverse=True)[:3]
    reason = (
        f"近{len(reference_years)}年参考数据，院校/专业参考位次约为 {reference_rank}。"
        if reference_rank
        else f"缺少位次，采用分数参考，最近最低分 {first.min_score}。"
    )
    if is_whitelisted:
        reason = f"{reason} 当前院校命中白名单关注。"
    snapshot = {
        "reference_years": reference_years,
        "latest_year": first.year,
        "latest_min_rank": first.min_rank,
        "latest_min_score": first.min_score,
        "province": first.province,
        "college_name": first.college.name if first.college else None,
        "major_name": first.major.name if first.major else None,
        "student_score": score_value,
        "student_rank": student_rank,
    }
    return RecommendationResult(
        student_id=student.id,
        exam_id=exam_id,
        scheme_id=scheme_id,
        result_type=result_type,
        college_id=first.college_id,
        major_id=first.major_id,
        reference_rank=reference_rank,
        student_rank=student_rank,
        score_basis=score_basis,
        ratio=ratio,
        reason_text=reason,
        risk_flags_json=risk_flags or None,
        snapshot_json=snapshot,
    )


def _filter_candidates(
    session: Session,
    *,
    province: str,
    student: Student,
    student_type: str,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
) -> list[AdmissionRecord]:
    items = list_admission_candidates(
        session,
        province=province,
        student_type="general" if student_type == "general" else student_type,
        subject_requirement=subject_combination,
    )
    filtered: list[AdmissionRecord] = []
    whitelist_ids = set(settings.whitelist_college_ids)
    blacklist_ids = set(settings.blacklist_college_ids)
    for item in items:
        college = item.college
        major = item.major
        college_id = college.id if college else item.college_id
        if college_id in blacklist_ids and college_id not in whitelist_ids:
            continue
        is_whitelisted = college_id in whitelist_ids
        if target_regions and college and college.province not in target_regions and college.city not in target_regions and not is_whitelisted:
            continue
        if school_levels:
            level_tags = set(college.school_level_tags_json or []) if college else set()
            if not level_tags.intersection(set(school_levels)) and not is_whitelisted:
                continue
        if major_keyword and major and major_keyword not in major.name:
            continue
        if major_keyword and major is None and major_keyword:
            continue
        if student_type != "general":
            if college and not college.supports_art:
                continue
            if student.art_track and item.art_track and item.art_track != student.art_track:
                continue
        filtered.append(item)
    return filtered


def _get_student_exam_metrics(session: Session, student_id: int, exam_id: int) -> tuple[float, int | None]:
    snapshot = next(
        (item for item in get_total_snapshots_for_exam(session, exam_id) if item.student_id == student_id),
        None,
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="该学生在本次考试中暂无总分数据")
    return snapshot.total_score, snapshot.grade_rank


def _detect_student_type(student: Student) -> str:
    if student.art_track:
        return "art"
    if student.student_type and student.student_type not in {"general", "repeat"}:
        return student.student_type
    return "general"


def _load_recommendation_thresholds(session: Session) -> dict[str, float]:
    state = _load_recommendation_settings_state(session)
    return {
        "safe": state.safe_ratio_max,
        "steady": state.steady_ratio_max,
        "rush": state.rush_ratio_max,
    }


def _load_recommendation_settings_state(session: Session) -> RecommendationSettingsState:
    config_rows = _load_recommendation_config_rows(session)

    def read_float(key: str) -> float:
        value = config_rows.get(key).config_value if config_rows.get(key) else RECOMMENDATION_CONFIG_DEFAULTS[key][0]
        return float(value)

    def read_json_list(key: str) -> list[int]:
        raw_value = config_rows.get(key).config_value if config_rows.get(key) else RECOMMENDATION_CONFIG_DEFAULTS[key][0]
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            payload = []
        if not isinstance(payload, list):
            return []
        result: list[int] = []
        for item in payload:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return sorted(set(result))

    return RecommendationSettingsState(
        safe_ratio_max=read_float("safe_ratio_max"),
        steady_ratio_max=read_float("steady_ratio_max"),
        rush_ratio_max=read_float("rush_ratio_max"),
        whitelist_college_ids=read_json_list("whitelist_college_ids_json"),
        blacklist_college_ids=read_json_list("blacklist_college_ids_json"),
    )


def _serialize_recommendation_settings(
    session: Session,
    state: RecommendationSettingsState,
) -> RecommendationSettingsRead:
    def load_college_options(ids: list[int]) -> list[RecommendationCollegeOption]:
        return _load_college_options(session, ids)

    return RecommendationSettingsRead(
        safe_ratio_max=state.safe_ratio_max,
        steady_ratio_max=state.steady_ratio_max,
        rush_ratio_max=state.rush_ratio_max,
        whitelist_college_ids=state.whitelist_college_ids,
        blacklist_college_ids=state.blacklist_college_ids,
        whitelist_colleges=load_college_options(state.whitelist_college_ids),
        blacklist_colleges=load_college_options(state.blacklist_college_ids),
        strategy_presets=_load_strategy_presets(session),
    )


def _load_recommendation_config_rows(session: Session) -> dict[str, ConfigItem]:
    return {
        row.config_key: row
        for row in session.scalars(select(ConfigItem).where(ConfigItem.config_group == "recommendation")).all()
    }


def _upsert_recommendation_config_values(session: Session, values: dict[str, str]) -> None:
    config_rows = _load_recommendation_config_rows(session)
    for key, (default_value, value_type, description) in RECOMMENDATION_CONFIG_DEFAULTS.items():
        row = config_rows.get(key)
        if row:
            if key in values:
                row.config_value = values[key]
            elif row.config_value is None:
                row.config_value = default_value
            row.value_type = value_type
            row.description = description
        else:
            session.add(
                ConfigItem(
                    config_group="recommendation",
                    config_key=key,
                    config_value=values.get(key, default_value),
                    value_type=value_type,
                    description=description,
                )
            )
    session.flush()


def _validate_strategy_values(
    *,
    safe_ratio_max: float,
    steady_ratio_max: float,
    rush_ratio_max: float,
    whitelist_college_ids: list[int],
    blacklist_college_ids: list[int],
) -> None:
    if not (0 < safe_ratio_max <= steady_ratio_max <= rush_ratio_max):
        raise HTTPException(status_code=400, detail="推荐阈值需要满足 保 <= 稳 <= 冲")
    if set(whitelist_college_ids).intersection(set(blacklist_college_ids)):
        raise HTTPException(status_code=400, detail="同一院校不能同时存在于黑名单和白名单")


def _load_college_options(session: Session, ids: list[int]) -> list[RecommendationCollegeOption]:
    if not ids:
        return []
    rows = session.scalars(select(College).where(College.id.in_(ids), College.is_active.is_(True))).all()
    rows.sort(key=lambda item: ids.index(item.id))
    return [RecommendationCollegeOption(id=item.id, name=item.name) for item in rows]


def _load_strategy_preset_payloads(session: Session) -> list[dict[str, object]]:
    config_rows = _load_recommendation_config_rows(session)
    raw_value = (
        config_rows.get("strategy_presets_json").config_value
        if config_rows.get("strategy_presets_json")
        else RECOMMENDATION_CONFIG_DEFAULTS["strategy_presets_json"][0]
    )
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        payload = []
    return payload if isinstance(payload, list) else []


def _load_strategy_presets(session: Session) -> list[RecommendationStrategyPresetRead]:
    rows: list[RecommendationStrategyPresetRead] = []
    for item in _load_strategy_preset_payloads(session):
        whitelist_ids = [int(value) for value in item.get("whitelist_college_ids", []) if str(value).isdigit()]
        blacklist_ids = [int(value) for value in item.get("blacklist_college_ids", []) if str(value).isdigit()]
        try:
            created_at = datetime.fromisoformat(str(item.get("created_at")))
        except (TypeError, ValueError):
            created_at = datetime.now()
        rows.append(
            RecommendationStrategyPresetRead(
                id=str(item.get("id") or uuid4().hex),
                name=str(item.get("name") or "未命名模板"),
                note=str(item.get("note")) if item.get("note") else None,
                safe_ratio_max=float(item.get("safe_ratio_max", 0.85)),
                steady_ratio_max=float(item.get("steady_ratio_max", 1.0)),
                rush_ratio_max=float(item.get("rush_ratio_max", 1.15)),
                whitelist_college_ids=whitelist_ids,
                blacklist_college_ids=blacklist_ids,
                whitelist_colleges=_load_college_options(session, whitelist_ids),
                blacklist_colleges=_load_college_options(session, blacklist_ids),
                created_at=created_at,
            )
        )
    rows.sort(key=lambda item: item.created_at, reverse=True)
    return rows
