from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import GaokaoPathway, GaokaoPathwayRule, Student, StudentPathwayEvaluation, StudentPathwayProfile
from app.repositories.gaokao_pathways import (
    get_pathway,
    get_pathway_by_code,
    get_pathway_rule_by_code,
    get_student_pathway_evaluation,
    get_student_pathway_profile as repo_get_student_pathway_profile,
    list_pathway_rules as repo_list_pathway_rules,
    list_pathways as repo_list_pathways,
)
from app.repositories.system import write_audit_log
from app.schemas.gaokao_pathway import (
    GaokaoPathwayBootstrapResponse,
    GaokaoPathwayRead,
    GaokaoPathwayRulePayload,
    GaokaoPathwayRuleRead,
    StudentPathwayEvaluationRead,
    StudentPathwayEvaluationResponse,
    StudentPathwayProfilePayload,
    StudentPathwayProfileRead,
    StudentPathwayRuleEvaluationRead,
)


DEFAULT_PROVINCE = "山东"
DEFAULT_TARGET_YEAR = 2026

STATUS_LABELS = {
    "suitable": "适合关注",
    "possible": "可能适合",
    "not_recommended": "不建议",
    "insufficient_data": "信息不足",
    "manual_review": "需人工复核",
    "not_applicable": "当前不适用",
}

RULE_RESULT_PASSED = "passed"
RULE_RESULT_FAILED = "failed"
RULE_RESULT_UNKNOWN = "unknown"

_MISSING = object()


@dataclass(frozen=True)
class PathwaySeed:
    pathway_code: str
    pathway_name: str
    pathway_group: str
    student_type: str | None
    exam_type: str | None
    batch_name: str | None
    volunteer_mode: str | None
    max_volunteer_count: int | None
    recommendation_depth: str
    summary: str
    risk_level: str
    notes_json: dict[str, object]


PATHWAY_SEEDS: tuple[PathwaySeed, ...] = (
    PathwaySeed(
        pathway_code="summer_general_regular",
        pathway_name="普通类常规批",
        pathway_group="夏季高考",
        student_type="general",
        exam_type="summer_gaokao",
        batch_name="普通类常规批",
        volunteer_mode="专业（专业类）+学校",
        max_volunteer_count=96,
        recommendation_depth="full_rank_recommendation",
        summary="可接入现有山东普通类冲稳保推荐；正式填报前仍需核对 2026 官方计划和章程。",
        risk_level="medium",
        notes_json={"entry": "shandong_rush_stable_safe", "official_boundary": "最终以官方发布和高校章程为准"},
    ),
    PathwaySeed(
        "summer_general_early_a",
        "普通类提前批A类",
        "提前批",
        "general",
        "summer_gaokao",
        "普通类提前批A类",
        "院校或专业志愿，按当年政策核验",
        None,
        "eligibility_screening",
        "用于军事、公安政法、飞行技术、航海、消防救援等方向的资格提醒。",
        "high",
        {"boundary": "只做资格初筛，不给录取概率"},
    ),
    PathwaySeed(
        "summer_general_early_b",
        "普通类提前批B类",
        "提前批",
        "general",
        "summer_gaokao",
        "普通类提前批B类",
        "专业（专业类）+学校或政策指定模式",
        None,
        "eligibility_screening",
        "用于公费师范生、省属公费生、定向就业等路径的规则提醒。",
        "high",
        {"boundary": "需人工核对定向就业、签约和服务年限"},
    ),
    PathwaySeed(
        "summer_special_type",
        "普通类特殊类型批",
        "特殊类型",
        "general",
        "summer_gaokao",
        "特殊类型批",
        "资格高校相关志愿",
        None,
        "eligibility_screening",
        "用于高校专项等需资格审核路径的资格提醒。",
        "high",
        {"boundary": "资格名单、前置报名和高校测试必须人工核验"},
    ),
    PathwaySeed(
        "spring_exam_undergrad",
        "春季高考本科批",
        "春季高考",
        "spring_exam",
        "spring_gaokao",
        "春季高考本科批",
        "专业类别内填报",
        None,
        "eligibility_screening",
        "春季高考路径必须核对专业类别和对应分数线。",
        "high",
        {"boundary": "缺专门录取结果时只能初筛"},
    ),
    PathwaySeed(
        "spring_exam_junior",
        "春季高考专科批",
        "春季高考",
        "spring_exam",
        "spring_gaokao",
        "春季高考专科批",
        "专业类别内填报",
        None,
        "eligibility_screening",
        "春季高考专科路径必须核对专业类别和院校章程。",
        "high",
        {"boundary": "缺专门录取结果时只能初筛"},
    ),
    PathwaySeed(
        "vocational_single_exam",
        "高职单独招生",
        "高职分类招生",
        "vocational_or_social",
        "vocational_single_exam",
        "高职单独招生",
        "院校报名与测试",
        None,
        "eligibility_screening",
        "面向中职应届、社会人员等，重点核对报名、文化素质和专业技能测试。",
        "high",
        {"boundary": "不等同于夏季普通类常规批"},
    ),
    PathwaySeed(
        "vocational_comprehensive",
        "高职综合评价招生",
        "高职分类招生",
        "general",
        "vocational_comprehensive",
        "高职综合评价招生",
        "院校报名与素质测试",
        None,
        "eligibility_screening",
        "面向普通高中应届毕业生，重点核对综合素质评价和院校测试要求。",
        "high",
        {"boundary": "只做资格初筛和材料缺口提醒"},
    ),
    PathwaySeed(
        "art_undergrad",
        "艺术类本科批",
        "艺术体育",
        "art",
        "art_gaokao",
        "艺术类本科批",
        "按艺术类别和专业规则核验",
        None,
        "eligibility_screening",
        "艺术路径需核对统考、校考、文化线、综合分和章程限制。",
        "high",
        {"boundary": "不同院校录取原则不同，不能给统一概率"},
    ),
    PathwaySeed(
        "art_junior",
        "艺术类专科批",
        "艺术体育",
        "art",
        "art_gaokao",
        "艺术类专科批",
        "按艺术类别和专业规则核验",
        None,
        "eligibility_screening",
        "艺术专科路径需核对艺术类别、文化线和章程限制。",
        "high",
        {"boundary": "不同院校录取原则不同，不能给统一概率"},
    ),
    PathwaySeed(
        "sports_regular",
        "体育类常规批",
        "艺术体育",
        "sports",
        "sports_gaokao",
        "体育类常规批",
        "按体育综合分和批次规则核验",
        None,
        "eligibility_screening",
        "体育类常规批需核对体育专业成绩、综合分和兼报限制。",
        "high",
        {"boundary": "不要和体育单招或高水平运动队混淆"},
    ),
    PathwaySeed(
        "sports_single_exam",
        "体育单招",
        "艺术体育",
        "sports",
        "sports_single_exam",
        "体育单招",
        "专项报名系统",
        None,
        "policy_notice",
        "体育单招是独立路径，需要专项报名、文化考试和体育专项考试。",
        "high",
        {"boundary": "仅做路径提醒和材料清单"},
    ),
    PathwaySeed(
        "high_level_sports",
        "高水平运动队",
        "特殊类型",
        "sports",
        "high_level_sports",
        "高水平运动队",
        "资格审查和高校测试",
        None,
        "policy_notice",
        "高水平运动队需核对运动员等级、资格审核和高校招生简章。",
        "high",
        {"boundary": "仅做路径提醒和材料清单"},
    ),
)


def list_pathways(
    session: Session,
    *,
    province: str = DEFAULT_PROVINCE,
    include_inactive: bool = False,
) -> list[GaokaoPathwayRead]:
    return [
        _serialize_pathway(item)
        for item in repo_list_pathways(session, province=province, include_inactive=include_inactive)
    ]


def bootstrap_shandong_pathways(
    session: Session,
    *,
    target_year: int = DEFAULT_TARGET_YEAR,
) -> GaokaoPathwayBootstrapResponse:
    created_count = 0
    skipped_count = 0
    rule_created_count = 0
    rule_skipped_count = 0
    for seed in PATHWAY_SEEDS:
        pathway = get_pathway_by_code(session, province=DEFAULT_PROVINCE, pathway_code=seed.pathway_code)
        if pathway:
            skipped_count += 1
        else:
            pathway = GaokaoPathway(
                province=DEFAULT_PROVINCE,
                pathway_code=seed.pathway_code,
                pathway_name=seed.pathway_name,
                pathway_group=seed.pathway_group,
                student_type=seed.student_type,
                exam_type=seed.exam_type,
                batch_name=seed.batch_name,
                volunteer_mode=seed.volunteer_mode,
                max_volunteer_count=seed.max_volunteer_count,
                recommendation_depth=seed.recommendation_depth,
                status="active",
                summary=seed.summary,
                risk_level=seed.risk_level,
                notes_json=seed.notes_json,
            )
            session.add(pathway)
            session.flush()
            created_count += 1

        result = _ensure_baseline_rule(session, pathway, target_year)
        rule_created_count += result[0]
        rule_skipped_count += result[1]

    if created_count or rule_created_count:
        write_audit_log(
            session,
            module="gaokao_pathways",
            action="bootstrap_shandong_pathways",
            target_type="gaokao_pathway",
            target_id=str(target_year),
            detail_json={"created_count": created_count, "rule_created_count": rule_created_count},
        )

    return GaokaoPathwayBootstrapResponse(
        province=DEFAULT_PROVINCE,
        target_year=target_year,
        total_count=len(PATHWAY_SEEDS),
        created_count=created_count,
        skipped_count=skipped_count,
        rule_created_count=rule_created_count,
        rule_skipped_count=rule_skipped_count,
    )


def list_pathway_rules(
    session: Session,
    pathway_id: int,
) -> list[GaokaoPathwayRuleRead]:
    _ensure_pathway(session, pathway_id)
    return [_serialize_rule(item) for item in repo_list_pathway_rules(session, pathway_id=pathway_id)]


def create_pathway_rule(
    session: Session,
    pathway_id: int,
    payload: GaokaoPathwayRulePayload,
) -> GaokaoPathwayRuleRead:
    pathway = _ensure_pathway(session, pathway_id)
    _validate_rule_payload(payload)
    existing = get_pathway_rule_by_code(session, pathway_id=pathway.id, rule_code=payload.rule_code.strip())
    if existing:
        raise HTTPException(status_code=400, detail="该路径规则编码已存在")
    item = GaokaoPathwayRule(pathway_id=pathway.id, rule_code=payload.rule_code.strip())
    session.add(item)
    _apply_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="gaokao_pathways",
        action="create_pathway_rule",
        target_type="gaokao_pathway_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_rule(item)


def get_student_pathway_profile(
    session: Session,
    student_id: int,
    *,
    province: str = DEFAULT_PROVINCE,
) -> StudentPathwayProfileRead:
    student = _ensure_student(session, student_id)
    item = repo_get_student_pathway_profile(session, student_id=student_id, province=province)
    if item:
        return _serialize_profile(item, student)
    return _serialize_profile(_build_profile_from_student(student, province=province), student)


def upsert_student_pathway_profile(
    session: Session,
    student_id: int,
    payload: StudentPathwayProfilePayload,
) -> StudentPathwayProfileRead:
    student = _ensure_student(session, student_id)
    item = repo_get_student_pathway_profile(session, student_id=student_id, province=payload.province)
    if not item:
        item = StudentPathwayProfile(student_id=student_id, province=payload.province)
        session.add(item)
    _apply_profile_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="gaokao_pathways",
        action="upsert_student_pathway_profile",
        target_type="student_pathway_profile",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_profile(item, student)


def preview_student_pathway_evaluations(
    session: Session,
    student_id: int,
    *,
    target_year: int = DEFAULT_TARGET_YEAR,
    province: str = DEFAULT_PROVINCE,
) -> StudentPathwayEvaluationResponse:
    return _evaluate_student_pathways(
        session,
        student_id=student_id,
        target_year=target_year,
        province=province,
        persist=False,
    )


def persist_student_pathway_evaluations(
    session: Session,
    student_id: int,
    *,
    target_year: int = DEFAULT_TARGET_YEAR,
    province: str = DEFAULT_PROVINCE,
) -> StudentPathwayEvaluationResponse:
    return _evaluate_student_pathways(
        session,
        student_id=student_id,
        target_year=target_year,
        province=province,
        persist=True,
    )


def _evaluate_student_pathways(
    session: Session,
    *,
    student_id: int,
    target_year: int,
    province: str,
    persist: bool,
) -> StudentPathwayEvaluationResponse:
    student = _ensure_student(session, student_id)
    profile = repo_get_student_pathway_profile(session, student_id=student_id, province=province)
    if not profile:
        profile = _build_profile_from_student(student, province=province)
    pathways = repo_list_pathways(session, province=province)
    evaluations = [_evaluate_single_pathway(profile, pathway, target_year) for pathway in pathways]
    if persist:
        persisted = [
            _persist_evaluation(session, evaluation, pathway_id=evaluation.pathway_id)
            for evaluation in evaluations
        ]
        evaluations = persisted
        write_audit_log(
            session,
            module="gaokao_pathways",
            action="evaluate_student_pathways",
            target_type="student",
            target_id=str(student_id),
            detail_json={"target_year": target_year, "pathway_count": len(evaluations)},
        )
    return StudentPathwayEvaluationResponse(
        student_id=student_id,
        target_year=target_year,
        profile=_serialize_profile(profile, student),
        evaluations=evaluations,
    )


def _evaluate_single_pathway(
    profile: StudentPathwayProfile,
    pathway: GaokaoPathway,
    target_year: int,
) -> StudentPathwayEvaluationRead:
    active_rules = [
        rule
        for rule in pathway.rules
        if rule.is_active and _rule_is_valid_for_year(rule, target_year)
    ]
    rule_results = [_evaluate_rule(profile, rule) for rule in active_rules]
    matched_rules = [item for item in rule_results if item.result == RULE_RESULT_PASSED]
    hard_failures = [
        item
        for item in rule_results
        if item.result == RULE_RESULT_FAILED and item.rule_type == "hard_gate"
    ]
    hard_unknowns = [
        item
        for item in rule_results
        if item.result == RULE_RESULT_UNKNOWN and item.rule_type in {"hard_gate", "score_line", "subject_required"}
    ]
    warning_rules = [
        item
        for item in rule_results
        if item.result != RULE_RESULT_PASSED
        and item.rule_type in {"soft_warning", "manual_check", "chapter_check", "time_window", "material_required"}
    ]
    missing_materials = [
        {
            "rule_code": item.rule_code,
            "material_key": item.missing_material_key or item.rule_code,
            "message": item.message or item.rule_name,
        }
        for item in rule_results
        if item.result != RULE_RESULT_PASSED and item.rule_type == "material_required"
    ]
    manual_required = [
        item
        for item in rule_results
        if item.result == RULE_RESULT_UNKNOWN and item.manual_review_required
    ]
    status = _decide_status(
        pathway,
        hard_failures=hard_failures,
        hard_unknowns=hard_unknowns,
        missing_materials=missing_materials,
        manual_required=manual_required,
        warning_rules=warning_rules,
    )
    next_actions = _build_next_actions(
        pathway,
        hard_failures=hard_failures,
        hard_unknowns=hard_unknowns,
        warning_rules=warning_rules,
        missing_materials=missing_materials,
        manual_required=manual_required,
    )
    score = _calculate_score(
        hard_failure_count=len(hard_failures),
        unknown_count=len(hard_unknowns) + len(manual_required) + len(missing_materials),
        warning_count=len(warning_rules),
    )
    return StudentPathwayEvaluationRead(
        id=None,
        student_id=profile.student_id,
        pathway_id=pathway.id,
        target_year=target_year,
        pathway_code=pathway.pathway_code,
        pathway_name=pathway.pathway_name,
        pathway_group=pathway.pathway_group,
        status=status,
        status_label=STATUS_LABELS[status],
        score=score,
        confidence_level=_confidence_for_status(status),
        matched_rules_json=[item.model_dump() for item in matched_rules],
        failed_rules_json=[item.model_dump() for item in hard_failures],
        warning_rules_json=[item.model_dump() for item in warning_rules + hard_unknowns + manual_required],
        missing_materials_json=missing_materials,
        recommendation_depth=pathway.recommendation_depth,
        summary=_build_evaluation_summary(pathway, status, len(missing_materials), len(manual_required)),
        next_actions_json=next_actions,
        is_active=True,
    )


def _evaluate_rule(profile: StudentPathwayProfile, rule: GaokaoPathwayRule) -> StudentPathwayRuleEvaluationRead:
    result = _evaluate_condition(profile, rule.condition_json or {})
    missing_key = _extract_missing_material_key(rule.condition_json or {})
    return StudentPathwayRuleEvaluationRead(
        rule_id=rule.id,
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        severity=rule.severity,
        result=result,
        message=rule.message_template,
        manual_review_required=rule.manual_review_required,
        missing_material_key=missing_key if result != RULE_RESULT_PASSED else None,
    )


def _evaluate_condition(profile: StudentPathwayProfile, condition: dict[str, Any]) -> str:
    condition_type = str(condition.get("type") or "always_passed")
    if condition_type == "always_passed":
        return RULE_RESULT_PASSED
    if condition_type == "always_failed":
        return RULE_RESULT_FAILED
    if condition_type == "manual_review":
        return RULE_RESULT_UNKNOWN
    if condition_type == "field_present":
        value = _resolve_profile_value(profile, str(condition.get("field") or ""))
        return RULE_RESULT_PASSED if _has_value(value) else RULE_RESULT_UNKNOWN
    if condition_type == "field_equals":
        value = _resolve_profile_value(profile, str(condition.get("field") or ""))
        if not _has_value(value):
            return RULE_RESULT_UNKNOWN
        return RULE_RESULT_PASSED if value == condition.get("equals") else RULE_RESULT_FAILED
    if condition_type == "field_in":
        value = _resolve_profile_value(profile, str(condition.get("field") or ""))
        if not _has_value(value):
            return RULE_RESULT_UNKNOWN
        values = condition.get("values") or []
        return RULE_RESULT_PASSED if value in values else RULE_RESULT_FAILED
    if condition_type == "boolean_is":
        value = _resolve_profile_value(profile, str(condition.get("field") or ""))
        if value is _MISSING or value is None:
            return RULE_RESULT_UNKNOWN
        return RULE_RESULT_PASSED if bool(value) is bool(condition.get("value")) else RULE_RESULT_FAILED
    if condition_type == "material_present":
        key = str(condition.get("key") or "")
        value = (profile.materials_json or {}).get(key, _MISSING)
        return RULE_RESULT_PASSED if _has_value(value) and bool(value) else RULE_RESULT_UNKNOWN
    if condition_type == "all":
        results = [_evaluate_condition(profile, item) for item in _condition_items(condition)]
        if any(item == RULE_RESULT_FAILED for item in results):
            return RULE_RESULT_FAILED
        if any(item == RULE_RESULT_UNKNOWN for item in results):
            return RULE_RESULT_UNKNOWN
        return RULE_RESULT_PASSED
    if condition_type == "any":
        results = [_evaluate_condition(profile, item) for item in _condition_items(condition)]
        if any(item == RULE_RESULT_PASSED for item in results):
            return RULE_RESULT_PASSED
        if any(item == RULE_RESULT_UNKNOWN for item in results):
            return RULE_RESULT_UNKNOWN
        return RULE_RESULT_FAILED
    return RULE_RESULT_UNKNOWN


def _condition_items(condition: dict[str, Any]) -> list[dict[str, Any]]:
    items = condition.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _resolve_profile_value(profile: StudentPathwayProfile, field: str) -> object:
    if not field:
        return _MISSING
    if field.startswith("materials."):
        return (profile.materials_json or {}).get(field.removeprefix("materials."), _MISSING)
    if not hasattr(profile, field):
        return _MISSING
    return getattr(profile, field)


def _has_value(value: object) -> bool:
    if value is _MISSING or value is None:
        return False
    if value == "":
        return False
    if isinstance(value, (list, dict, tuple, set)) and not value:
        return False
    return True


def _extract_missing_material_key(condition: dict[str, Any]) -> str | None:
    if condition.get("type") == "material_present":
        key = condition.get("key")
        return str(key) if key else None
    if condition.get("type") == "field_present":
        field = condition.get("field")
        return str(field) if field else None
    return None


def _decide_status(
    pathway: GaokaoPathway,
    *,
    hard_failures: list[StudentPathwayRuleEvaluationRead],
    hard_unknowns: list[StudentPathwayRuleEvaluationRead],
    missing_materials: list[dict[str, object]],
    manual_required: list[StudentPathwayRuleEvaluationRead],
    warning_rules: list[StudentPathwayRuleEvaluationRead],
) -> str:
    if pathway.status == "not_supported":
        return "not_applicable"
    if hard_failures:
        return "not_recommended"
    if hard_unknowns or missing_materials:
        return "insufficient_data"
    if manual_required or pathway.recommendation_depth == "manual_review_required":
        return "manual_review"
    if warning_rules:
        return "possible"
    if pathway.recommendation_depth == "full_rank_recommendation":
        return "suitable"
    return "possible"


def _build_next_actions(
    pathway: GaokaoPathway,
    *,
    hard_failures: list[StudentPathwayRuleEvaluationRead],
    hard_unknowns: list[StudentPathwayRuleEvaluationRead],
    warning_rules: list[StudentPathwayRuleEvaluationRead],
    missing_materials: list[dict[str, object]],
    manual_required: list[StudentPathwayRuleEvaluationRead],
) -> list[str]:
    actions: list[str] = []
    for item in hard_failures + hard_unknowns + warning_rules + manual_required:
        message = item.message or item.rule_name
        if message and message not in actions:
            actions.append(message)
    for item in missing_materials:
        message = str(item.get("message") or "补齐路径所需材料后重新评估")
        if message not in actions:
            actions.append(message)
    if pathway.recommendation_depth == "full_rank_recommendation":
        actions.append("可进入山东普通类推荐工作台查看冲稳保候选，但正式填报前仍需核验 2026 官方计划和高校章程。")
    elif not actions:
        actions.append("先核对该路径的官方公告、报名时间、资格材料和目标院校章程。")
    return actions


def _calculate_score(
    *,
    hard_failure_count: int,
    unknown_count: int,
    warning_count: int,
) -> float:
    score = 100 - hard_failure_count * 60 - unknown_count * 12 - warning_count * 6
    return float(max(0, min(100, score)))


def _confidence_for_status(status: str) -> str:
    if status in {"suitable", "possible"}:
        return "medium"
    if status == "not_recommended":
        return "high"
    return "low"


def _build_evaluation_summary(
    pathway: GaokaoPathway,
    status: str,
    missing_count: int,
    manual_count: int,
) -> str:
    prefix = f"{pathway.pathway_name}：{STATUS_LABELS[status]}。"
    if status == "not_recommended":
        return prefix + "存在硬性门槛不满足，当前不建议作为主路径。"
    if missing_count:
        return prefix + f"还有 {missing_count} 项材料或画像信息缺失，补齐后再评估。"
    if manual_count or pathway.recommendation_depth != "full_rank_recommendation":
        return prefix + "该路径当前只做资格初筛或政策提醒，不能理解为录取概率。"
    return prefix + "可结合现有山东普通类冲稳保推荐继续查看候选。"


def _persist_evaluation(
    session: Session,
    evaluation: StudentPathwayEvaluationRead,
    *,
    pathway_id: int,
) -> StudentPathwayEvaluationRead:
    item = get_student_pathway_evaluation(
        session,
        student_id=evaluation.student_id,
        pathway_id=pathway_id,
        target_year=evaluation.target_year,
    )
    if not item:
        item = StudentPathwayEvaluation(
            student_id=evaluation.student_id,
            pathway_id=pathway_id,
            target_year=evaluation.target_year,
        )
        session.add(item)
    item.status = evaluation.status
    item.status_label = evaluation.status_label
    item.score = evaluation.score
    item.confidence_level = evaluation.confidence_level
    item.matched_rules_json = evaluation.matched_rules_json
    item.failed_rules_json = evaluation.failed_rules_json
    item.warning_rules_json = evaluation.warning_rules_json
    item.missing_materials_json = evaluation.missing_materials_json
    item.recommendation_depth = evaluation.recommendation_depth
    item.summary = evaluation.summary
    item.next_actions_json = evaluation.next_actions_json
    item.is_active = True
    session.flush()
    session.refresh(item)
    return _serialize_evaluation(item)


def _ensure_baseline_rule(
    session: Session,
    pathway: GaokaoPathway,
    target_year: int,
) -> tuple[int, int]:
    if pathway.recommendation_depth == "full_rank_recommendation":
        return _ensure_rule_from_payload(
            session,
            pathway,
            GaokaoPathwayRulePayload(
                rule_code="d1_profile_candidate_type",
                rule_name="普通类路径画像确认",
                rule_type="hard_gate",
                severity="required",
                condition_json={"type": "field_in", "field": "candidate_type", "values": ["general", "普通类"]},
                message_template="学生画像需确认为山东普通类考生，才能进入普通类常规批推荐。",
                valid_from_year=target_year,
            ),
        )
    return _ensure_rule_from_payload(
        session,
        pathway,
        GaokaoPathwayRulePayload(
            rule_code="d1_manual_review_boundary",
            rule_name="路径人工复核边界",
            rule_type="manual_check",
            severity="review",
            condition_json={"type": "manual_review"},
            message_template="该路径需要核对官方公告、报名时间、资格材料和高校章程；当前只能做初筛或提醒。",
            manual_review_required=True,
            valid_from_year=target_year,
        ),
    )


def _ensure_rule_from_payload(
    session: Session,
    pathway: GaokaoPathway,
    payload: GaokaoPathwayRulePayload,
) -> tuple[int, int]:
    existing = get_pathway_rule_by_code(session, pathway_id=pathway.id, rule_code=payload.rule_code)
    if existing:
        return (0, 1)
    rule = GaokaoPathwayRule(pathway_id=pathway.id, rule_code=payload.rule_code)
    session.add(rule)
    _apply_rule_payload(rule, payload)
    return (1, 0)


def _ensure_pathway(session: Session, pathway_id: int) -> GaokaoPathway:
    pathway = get_pathway(session, pathway_id)
    if not pathway:
        raise HTTPException(status_code=404, detail="升学路径不存在")
    return pathway


def _ensure_student(session: Session, student_id: int) -> Student:
    student = session.get(Student, student_id)
    if not student or not student.is_active:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


def _validate_rule_payload(payload: GaokaoPathwayRulePayload) -> None:
    if not payload.rule_code.strip():
        raise HTTPException(status_code=400, detail="规则编码不能为空")
    if not payload.rule_name.strip():
        raise HTTPException(status_code=400, detail="规则名称不能为空")
    if payload.rule_type not in {
        "hard_gate",
        "soft_warning",
        "material_required",
        "time_window",
        "score_line",
        "subject_required",
        "category_match",
        "chapter_check",
        "manual_check",
    }:
        raise HTTPException(status_code=400, detail="规则类型不支持")
    if payload.valid_from_year and payload.valid_to_year and payload.valid_from_year > payload.valid_to_year:
        raise HTTPException(status_code=400, detail="规则有效年份范围不正确")


def _apply_rule_payload(item: GaokaoPathwayRule, payload: GaokaoPathwayRulePayload) -> None:
    item.rule_code = payload.rule_code.strip()
    item.rule_name = payload.rule_name.strip()
    item.rule_type = payload.rule_type
    item.severity = payload.severity
    item.condition_json = payload.condition_json or {}
    item.message_template = payload.message_template
    item.source_document_id = payload.source_document_id
    item.manual_review_required = payload.manual_review_required
    item.valid_from_year = payload.valid_from_year
    item.valid_to_year = payload.valid_to_year
    item.is_active = payload.is_active


def _apply_profile_payload(item: StudentPathwayProfile, payload: StudentPathwayProfilePayload) -> None:
    for field, value in payload.model_dump().items():
        setattr(item, field, value)


def _build_profile_from_student(student: Student, *, province: str) -> StudentPathwayProfile:
    candidate_type = student.student_type or "general"
    if student.art_track:
        candidate_type = "art"
    return StudentPathwayProfile(
        student_id=student.id,
        province=student.origin_province or province,
        candidate_type=candidate_type,
        art_track=student.art_track,
        materials_json={},
        career_preferences_json={},
        region_preferences_json={},
        family_constraints_json={},
        known_body_limitations_json={},
        is_active=True,
    )


def _rule_is_valid_for_year(rule: GaokaoPathwayRule, target_year: int) -> bool:
    if rule.valid_from_year is not None and target_year < rule.valid_from_year:
        return False
    if rule.valid_to_year is not None and target_year > rule.valid_to_year:
        return False
    return True


def _serialize_pathway(item: GaokaoPathway) -> GaokaoPathwayRead:
    return GaokaoPathwayRead(
        id=item.id,
        province=item.province,
        pathway_code=item.pathway_code,
        pathway_name=item.pathway_name,
        pathway_group=item.pathway_group,
        student_type=item.student_type,
        exam_type=item.exam_type,
        batch_name=item.batch_name,
        volunteer_mode=item.volunteer_mode,
        max_volunteer_count=item.max_volunteer_count,
        recommendation_depth=item.recommendation_depth,
        status=item.status,
        source_document_id=item.source_document_id,
        summary=item.summary,
        risk_level=item.risk_level,
        notes_json=item.notes_json or {},
        rules=[_serialize_rule(rule) for rule in item.rules if rule.is_active],
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_rule(item: GaokaoPathwayRule) -> GaokaoPathwayRuleRead:
    return GaokaoPathwayRuleRead(
        id=item.id,
        pathway_id=item.pathway_id,
        rule_code=item.rule_code,
        rule_name=item.rule_name,
        rule_type=item.rule_type,
        severity=item.severity,
        condition_json=item.condition_json or {},
        message_template=item.message_template,
        source_document_id=item.source_document_id,
        manual_review_required=item.manual_review_required,
        valid_from_year=item.valid_from_year,
        valid_to_year=item.valid_to_year,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_profile(item: StudentPathwayProfile, student: Student | None = None) -> StudentPathwayProfileRead:
    return StudentPathwayProfileRead(
        id=item.id,
        student_id=item.student_id,
        student_name=student.name if student else item.student.name if item.student else None,
        province=item.province,
        candidate_type=item.candidate_type,
        exam_type=item.exam_type,
        subject_combination=item.subject_combination,
        spring_exam_category=item.spring_exam_category,
        art_track=item.art_track,
        sports_track=item.sports_track,
        has_gaokao_registration=item.has_gaokao_registration,
        is_fresh_graduate=item.is_fresh_graduate,
        is_vocational_student=item.is_vocational_student,
        is_social_candidate=item.is_social_candidate,
        has_high_school_equivalent=item.has_high_school_equivalent,
        accept_private_college=item.accept_private_college,
        accept_sino_foreign=item.accept_sino_foreign,
        accept_junior_college=item.accept_junior_college,
        accept_outside_province=item.accept_outside_province,
        accept_early_batch=item.accept_early_batch,
        accept_service_commitment=item.accept_service_commitment,
        accept_interview_or_physical_test=item.accept_interview_or_physical_test,
        career_preferences_json=item.career_preferences_json or {},
        region_preferences_json=item.region_preferences_json or {},
        family_constraints_json=item.family_constraints_json or {},
        known_body_limitations_json=item.known_body_limitations_json or {},
        materials_json=item.materials_json or {},
        note=item.note,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_evaluation(item: StudentPathwayEvaluation) -> StudentPathwayEvaluationRead:
    pathway = item.pathway
    return StudentPathwayEvaluationRead(
        id=item.id,
        student_id=item.student_id,
        pathway_id=item.pathway_id,
        target_year=item.target_year,
        pathway_code=pathway.pathway_code if pathway else None,
        pathway_name=pathway.pathway_name if pathway else None,
        pathway_group=pathway.pathway_group if pathway else None,
        status=item.status,
        status_label=item.status_label,
        score=item.score,
        confidence_level=item.confidence_level,
        matched_rules_json=item.matched_rules_json or [],
        failed_rules_json=item.failed_rules_json or [],
        warning_rules_json=item.warning_rules_json or [],
        missing_materials_json=item.missing_materials_json or [],
        recommendation_depth=item.recommendation_depth,
        summary=item.summary,
        next_actions_json=item.next_actions_json or [],
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )
