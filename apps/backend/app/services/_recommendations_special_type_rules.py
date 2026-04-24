from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import EnrollmentPlan, SpecialTypeRule
from app.schemas.recommendation import SpecialTypeRulePayload


@dataclass(frozen=True)
class SpecialTypeRuleDefinition:
    province: str
    year: int
    student_type: str
    category_code: str
    category_label: str
    sort_order: int | None
    match_keywords: tuple[str, ...]
    review_notes: tuple[str, ...]
    priority_bonus: int
    priority_notes: tuple[str, ...]
    source_note: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class SpecialTypeContext:
    category_label: str | None
    review_notes: list[str]
    priority_bonus: int
    priority_notes: list[str]
    rule_code: str | None = None
    source_note: str | None = None


class _RuleLike(Protocol):
    province: str
    year: int
    student_type: str
    category_code: str
    category_label: str
    sort_order: int | None
    match_keywords_json: list[str] | None
    review_notes_json: list[str] | None
    priority_bonus: int
    priority_notes_json: list[str] | None
    source_note: str | None
    note: str | None


BASELINE_SOURCE_NOTE = "系统基线：山东特殊类型 fallback 规则字典，需结合官方章程继续校准。"


def build_special_type_rule_baselines(year: int) -> list[SpecialTypeRulePayload]:
    return [
        SpecialTypeRulePayload(
            province=rule.province,
            year=rule.year,
            student_type=rule.student_type,
            category_code=rule.category_code,
            category_label=rule.category_label,
            sort_order=rule.sort_order,
            match_keywords_json=list(rule.match_keywords),
            review_notes_json=list(rule.review_notes),
            priority_bonus=rule.priority_bonus,
            priority_notes_json=list(rule.priority_notes),
            source_note=rule.source_note,
            note=rule.note,
            is_active=True,
        )
        for rule in _build_shandong_special_type_rule_definitions(year)
    ]


def resolve_special_type_context(
    session: Session,
    *,
    plan: EnrollmentPlan,
    student_type: str,
) -> SpecialTypeContext:
    db_rules = _load_special_type_rules(session, plan=plan, student_type=student_type)
    if db_rules:
        return build_special_type_context(plan=plan, student_type=student_type, rules=db_rules)
    return build_special_type_context(plan=plan, student_type=student_type, rules=None)


def build_special_type_context(
    *,
    plan: EnrollmentPlan,
    student_type: str,
    rules: list[_RuleLike] | None = None,
) -> SpecialTypeContext:
    normalized_type = (student_type or "").strip()
    if normalized_type not in {"spring_exam", "comprehensive_evaluation", "independent_recruitment", "art", "sports"}:
        return SpecialTypeContext(category_label=None, review_notes=[], priority_bonus=0, priority_notes=[])

    definitions = (
        [_definition_from_model(rule) for rule in rules]
        if rules
        else _build_shandong_special_type_rule_definitions(int(plan.year or 0), student_type=normalized_type)
    )
    definitions = [rule for rule in definitions if rule.student_type == normalized_type]
    if not definitions:
        return SpecialTypeContext(category_label=None, review_notes=[], priority_bonus=0, priority_notes=[])

    text = _build_plan_match_text(plan)
    catchall: SpecialTypeRuleDefinition | None = None
    for rule in sorted(definitions, key=lambda item: (item.sort_order is None, item.sort_order or 9999, item.category_code)):
        keywords = [keyword.strip() for keyword in rule.match_keywords if keyword.strip()]
        if not keywords:
            catchall = catchall or rule
            continue
        if any(keyword in text for keyword in keywords):
            return _context_from_definition(rule)

    return _context_from_definition(catchall) if catchall else SpecialTypeContext(
        category_label=None,
        review_notes=[],
        priority_bonus=0,
        priority_notes=[],
    )


def _load_special_type_rules(
    session: Session,
    *,
    plan: EnrollmentPlan,
    student_type: str,
) -> list[SpecialTypeRule]:
    stmt = (
        select(SpecialTypeRule)
        .where(
            SpecialTypeRule.is_active.is_(True),
            SpecialTypeRule.province == plan.province,
            SpecialTypeRule.student_type == student_type,
            SpecialTypeRule.year <= plan.year,
        )
        .order_by(
            desc(SpecialTypeRule.year),
            SpecialTypeRule.sort_order.is_(None),
            SpecialTypeRule.sort_order,
            SpecialTypeRule.category_code,
            SpecialTypeRule.id,
        )
    )
    rows = list(session.scalars(stmt).all())
    if not rows:
        return []
    latest_year = rows[0].year
    return [row for row in rows if row.year == latest_year]


def _context_from_definition(rule: SpecialTypeRuleDefinition) -> SpecialTypeContext:
    return SpecialTypeContext(
        category_label=rule.category_label,
        review_notes=list(rule.review_notes),
        priority_bonus=rule.priority_bonus,
        priority_notes=list(rule.priority_notes),
        rule_code=rule.category_code,
        source_note=rule.source_note,
    )


def _definition_from_model(rule: _RuleLike) -> SpecialTypeRuleDefinition:
    return SpecialTypeRuleDefinition(
        province=rule.province,
        year=rule.year,
        student_type=rule.student_type,
        category_code=rule.category_code,
        category_label=rule.category_label,
        sort_order=rule.sort_order,
        match_keywords=tuple(rule.match_keywords_json or []),
        review_notes=tuple(rule.review_notes_json or []),
        priority_bonus=rule.priority_bonus,
        priority_notes=tuple(rule.priority_notes_json or []),
        source_note=rule.source_note,
        note=rule.note,
    )


def _build_plan_match_text(plan: EnrollmentPlan) -> str:
    college = plan.college
    major = plan.major
    return " ".join(
        segment.strip()
        for segment in [
            college.name if college else None,
            college.school_type if college else None,
            " ".join(college.school_level_tags_json or []) if college else None,
            major.name if major else None,
            major.category if major else None,
            major.direction if major else None,
            major.career_path if major else None,
            major.note if major else None,
            plan.batch,
            plan.major_name_snapshot,
            plan.subject_requirement,
            plan.source_note,
            plan.import_batch_name,
        ]
        if segment and segment.strip()
    )


def _rule(
    *,
    year: int,
    student_type: str,
    category_code: str,
    category_label: str,
    sort_order: int,
    keywords: tuple[str, ...],
    review_notes: tuple[str, ...],
    priority_bonus: int,
    priority_notes: tuple[str, ...],
    note: str | None = None,
) -> SpecialTypeRuleDefinition:
    return SpecialTypeRuleDefinition(
        province="山东",
        year=year,
        student_type=student_type,
        category_code=category_code,
        category_label=category_label,
        sort_order=sort_order,
        match_keywords=keywords,
        review_notes=review_notes,
        priority_bonus=priority_bonus,
        priority_notes=priority_notes,
        source_note=BASELINE_SOURCE_NOTE,
        note=note,
    )


def _build_shandong_special_type_rule_definitions(
    year: int,
    *,
    student_type: str | None = None,
) -> list[SpecialTypeRuleDefinition]:
    target_year = year or 2026
    rules = [
        *_spring_exam_rules(target_year),
        *_comprehensive_evaluation_rules(target_year),
        *_independent_recruitment_rules(target_year),
        *_art_rules(target_year),
        *_sports_rules(target_year),
    ]
    normalized_type = (student_type or "").strip()
    return [rule for rule in rules if not normalized_type or rule.student_type == normalized_type]


def _spring_exam_rules(year: int) -> list[SpecialTypeRuleDefinition]:
    common_notes = (
        "核对春考专业类别与技能考试类别是否一致",
        "核对春考本科/专科批次和填报单位规则",
    )
    return [
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_it",
            category_label="春考信息技术类",
            sort_order=10,
            keywords=("计算机", "软件", "网络", "大数据", "人工智能", "信息安全", "数字媒体", "物联网"),
            review_notes=(*common_notes, "核对信息技术类技能测试方向"),
            priority_bonus=9,
            priority_notes=("命中春考信息技术类字典，优先比对技能类别和专业方向。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_manufacturing",
            category_label="春考设备制造类",
            sort_order=20,
            keywords=("机械", "机电", "数控", "模具", "智能制造", "工业机器人", "自动化", "电气", "汽车"),
            review_notes=(*common_notes, "核对设备制造类或机电技术类技能测试方向"),
            priority_bonus=9,
            priority_notes=("命中春考设备制造类字典，优先核对设备/机电技能类别。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_medical",
            category_label="春考医药护理类",
            sort_order=30,
            keywords=("护理", "医学", "药", "康复", "口腔", "临床", "中药", "医学检验"),
            review_notes=(*common_notes, "核对医药护理类资格、体检和技能测试要求"),
            priority_bonus=8,
            priority_notes=("命中春考医药护理类字典，需同步核对体检和职业资格限制。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_finance_trade",
            category_label="春考财经商贸类",
            sort_order=40,
            keywords=("会计", "财务", "金融", "商务", "市场营销", "电子商务", "国际经济", "大数据与会计"),
            review_notes=(*common_notes, "核对财经商贸类技能测试方向"),
            priority_bonus=8,
            priority_notes=("命中春考财经商贸类字典，优先核对商贸/财会方向。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_construction",
            category_label="春考土建施工类",
            sort_order=50,
            keywords=("建筑", "工程造价", "建设", "土木", "施工", "装配式"),
            review_notes=(*common_notes, "核对土建施工类技能测试和身体条件要求"),
            priority_bonus=7,
            priority_notes=("命中春考土建施工类字典，需核对技能类别和实训条件。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_education",
            category_label="春考教育服务类",
            sort_order=60,
            keywords=("学前教育", "早期教育", "小学教育", "婴幼儿", "教育"),
            review_notes=(*common_notes, "核对教育服务类面试、体检或资格要求"),
            priority_bonus=7,
            priority_notes=("命中春考教育服务类字典，需核对面试和教师资格路径。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_tourism_service",
            category_label="春考旅游服务类",
            sort_order=70,
            keywords=("旅游", "酒店", "烹饪", "空乘", "航空服务"),
            review_notes=(*common_notes, "核对旅游服务类面试、身高或形象要求"),
            priority_bonus=7,
            priority_notes=("命中春考旅游服务类字典，需核对面试和身体条件。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_agriculture_food",
            category_label="春考农林食品类",
            sort_order=80,
            keywords=("农业", "农学", "园艺", "畜牧", "动物医学", "食品"),
            review_notes=(*common_notes, "核对农林食品类技能测试方向"),
            priority_bonus=6,
            priority_notes=("命中春考农林食品类字典，优先核对技能类别。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_transport",
            category_label="春考交通运输类",
            sort_order=90,
            keywords=("铁道", "轨道", "交通", "航空", "航海", "车辆", "物流"),
            review_notes=(*common_notes, "核对交通运输类身体条件、专业限制和技能类别"),
            priority_bonus=6,
            priority_notes=("命中春考交通运输类字典，需核对身体条件和技能类别。",),
        ),
        _rule(
            year=year,
            student_type="spring_exam",
            category_code="spring_unclear",
            category_label="春考专业类别待核",
            sort_order=999,
            keywords=(),
            review_notes=common_notes,
            priority_bonus=0,
            priority_notes=("未命中春考细分类别字典，必须人工确认专业类别。",),
        ),
    ]


def _comprehensive_evaluation_rules(year: int) -> list[SpecialTypeRuleDefinition]:
    common_notes = (
        "核对综合评价报名条件、校测安排和成绩折算规则",
        "核对学校章程中的综合评价录取办法",
    )
    return [
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_engineering",
            category_label="综评工科方向",
            sort_order=10,
            keywords=("智能制造", "装备制造", "机械", "计算机", "软件", "电子", "自动化", "电气", "人工智能"),
            review_notes=(*common_notes, "核对工科方向校测科目、实践能力或单科要求"),
            priority_bonus=8,
            priority_notes=("命中综评工科方向字典，优先核对校测和折算比例。",),
        ),
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_medical_health",
            category_label="综评医学健康方向",
            sort_order=20,
            keywords=("护理", "医学", "药", "康复", "口腔", "临床", "健康"),
            review_notes=(*common_notes, "核对医学健康方向体检、选科和资格限制"),
            priority_bonus=7,
            priority_notes=("命中综评医学健康方向字典，需同步核对体检和选科限制。",),
        ),
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_finance_trade",
            category_label="综评财经商贸方向",
            sort_order=30,
            keywords=("会计", "财务", "金融", "商务", "市场营销", "电子商务", "国际经济"),
            review_notes=(*common_notes, "核对财经商贸方向综合素质材料要求"),
            priority_bonus=7,
            priority_notes=("命中综评财经商贸方向字典，需核对综合素质材料。",),
        ),
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_education_service",
            category_label="综评教育服务方向",
            sort_order=40,
            keywords=("教育", "学前", "早期教育", "婴幼儿"),
            review_notes=(*common_notes, "核对教育服务方向面试、体检和资格路径"),
            priority_bonus=6,
            priority_notes=("命中综评教育服务方向字典，需核对面试和资格路径。",),
        ),
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_modern_service",
            category_label="综评现代服务方向",
            sort_order=50,
            keywords=("旅游", "酒店", "物流", "航空服务", "公共管理", "法律"),
            review_notes=(*common_notes, "核对现代服务方向面试或职业适应性要求"),
            priority_bonus=6,
            priority_notes=("命中综评现代服务方向字典，需核对面试或职业适应性要求。",),
        ),
        _rule(
            year=year,
            student_type="comprehensive_evaluation",
            category_code="ce_general",
            category_label="综合评价招生",
            sort_order=999,
            keywords=(),
            review_notes=common_notes,
            priority_bonus=0,
            priority_notes=("未命中综评细分方向字典，按综合评价通用清单复核。",),
        ),
    ]


def _independent_recruitment_rules(year: int) -> list[SpecialTypeRuleDefinition]:
    common_notes = (
        "核对单招报名条件、校测或职业适应性测试要求",
        "核对是否与夏季高考志愿填报规则冲突",
    )
    return [
        _rule(
            year=year,
            student_type="independent_recruitment",
            category_code="ir_technical_skill",
            category_label="单招技术技能方向",
            sort_order=10,
            keywords=("机械", "制造", "计算机", "软件", "电子", "自动化", "建筑", "机电"),
            review_notes=(*common_notes, "核对技术技能方向职业适应性测试内容"),
            priority_bonus=8,
            priority_notes=("命中单招技术技能方向字典，优先核对职业适应性测试。",),
        ),
        _rule(
            year=year,
            student_type="independent_recruitment",
            category_code="ir_modern_service",
            category_label="单招现代服务方向",
            sort_order=20,
            keywords=("旅游", "酒店", "商务", "营销", "物流", "航空服务"),
            review_notes=(*common_notes, "核对现代服务方向面试、身高或形象要求"),
            priority_bonus=7,
            priority_notes=("命中单招现代服务方向字典，需核对面试和身体条件。",),
        ),
        _rule(
            year=year,
            student_type="independent_recruitment",
            category_code="ir_finance_trade",
            category_label="单招财经商贸方向",
            sort_order=30,
            keywords=("会计", "金融", "电商", "财务", "电子商务"),
            review_notes=(*common_notes, "核对财经商贸方向测试内容和证书要求"),
            priority_bonus=7,
            priority_notes=("命中单招财经商贸方向字典，需核对测试内容。",),
        ),
        _rule(
            year=year,
            student_type="independent_recruitment",
            category_code="ir_medical_care",
            category_label="单招医药护理方向",
            sort_order=40,
            keywords=("护理", "医学", "药", "康复", "口腔"),
            review_notes=(*common_notes, "核对医药护理方向体检、资格和面试要求"),
            priority_bonus=7,
            priority_notes=("命中单招医药护理方向字典，需核对体检和资格限制。",),
        ),
        _rule(
            year=year,
            student_type="independent_recruitment",
            category_code="ir_general",
            category_label="单独招生",
            sort_order=999,
            keywords=(),
            review_notes=common_notes,
            priority_bonus=0,
            priority_notes=("未命中单招细分方向字典，按单招通用清单复核。",),
        ),
    ]


def _art_rules(year: int) -> list[SpecialTypeRuleDefinition]:
    common_notes = (
        "核对艺术统考类别、综合分折算和投档规则",
        "核对专业是否要求校考或单科/身体条件",
    )
    return [
        _rule(
            year=year,
            student_type="art",
            category_code="art_music",
            category_label="艺术音乐类",
            sort_order=10,
            keywords=("音乐", "声乐", "器乐", "作曲"),
            review_notes=(*common_notes, "核对音乐类统考方向、主项和校考要求"),
            priority_bonus=8,
            priority_notes=("命中艺术音乐类字典，需核对统考方向和主项。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_fine_design",
            category_label="艺术美术设计类",
            sort_order=20,
            keywords=("美术", "绘画", "设计", "视觉", "动画", "雕塑", "环境设计", "产品设计"),
            review_notes=(*common_notes, "核对美术与设计类统考类别和色觉要求"),
            priority_bonus=8,
            priority_notes=("命中艺术美术设计类字典，需核对统考类别和色觉限制。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_dance_performance",
            category_label="艺术舞蹈表演类",
            sort_order=30,
            keywords=("舞蹈", "表演", "戏剧", "戏曲", "导演", "舞台"),
            review_notes=(*common_notes, "核对舞蹈/表演类统考、校考和身高要求"),
            priority_bonus=7,
            priority_notes=("命中艺术舞蹈表演类字典，需核对身高和校考要求。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_broadcast_host",
            category_label="艺术播音主持类",
            sort_order=40,
            keywords=("播音", "主持", "新闻传播"),
            review_notes=(*common_notes, "核对播音主持类统考、校考和形象要求"),
            priority_bonus=7,
            priority_notes=("命中艺术播音主持类字典，需核对统考和形象条件。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_film_media",
            category_label="艺术编导影视类",
            sort_order=50,
            keywords=("广播电视编导", "影视", "摄影", "录音", "戏剧影视文学", "数字媒体艺术"),
            review_notes=(*common_notes, "核对编导影视类文化线、统考或校考口径"),
            priority_bonus=6,
            priority_notes=("命中艺术编导影视类字典，需核对文化线和统考/校考口径。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_calligraphy",
            category_label="艺术书法类",
            sort_order=60,
            keywords=("书法",),
            review_notes=(*common_notes, "核对书法类统考类别和文化线口径"),
            priority_bonus=6,
            priority_notes=("命中艺术书法类字典，需核对书法类统考口径。",),
        ),
        _rule(
            year=year,
            student_type="art",
            category_code="art_general",
            category_label="艺术类",
            sort_order=999,
            keywords=(),
            review_notes=common_notes,
            priority_bonus=0,
            priority_notes=("未命中艺术细分类别字典，需人工确认统考/校考类别。",),
        ),
    ]


def _sports_rules(year: int) -> list[SpecialTypeRuleDefinition]:
    common_notes = (
        "核对体育专业测试成绩、综合分折算和投档规则",
        "核对体育类本科/专科控制线口径",
    )
    return [
        _rule(
            year=year,
            student_type="sports",
            category_code="sports_education",
            category_label="体育教育类",
            sort_order=10,
            keywords=("体育教育", "社会体育", "运动康复", "体能训练", "休闲体育"),
            review_notes=(*common_notes, "核对体育专业测试分和综合分折算"),
            priority_bonus=6,
            priority_notes=("命中体育教育类字典，需核对体育专业测试分。",),
        ),
        _rule(
            year=year,
            student_type="sports",
            category_code="sports_training",
            category_label="运动训练类",
            sort_order=20,
            keywords=("运动训练", "武术", "民族传统体育", "竞技体育"),
            review_notes=(*common_notes, "核对运动训练类报名、专项测试和单招规则"),
            priority_bonus=6,
            priority_notes=("命中运动训练类字典，需核对专项测试和单招规则。",),
        ),
        _rule(
            year=year,
            student_type="sports",
            category_code="sports_general",
            category_label="体育类",
            sort_order=999,
            keywords=(),
            review_notes=common_notes,
            priority_bonus=0,
            priority_notes=("未命中体育细分类别字典，按体育类通用清单复核。",),
        ),
    ]
