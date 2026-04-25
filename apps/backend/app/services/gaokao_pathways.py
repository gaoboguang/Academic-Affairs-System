from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
from app.services.gaokao_imports import GaokaoSourceDocumentSeed, upsert_gaokao_source_document


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
    source_key: str = "shandong_2026_registration"


@dataclass(frozen=True)
class PolicySourceSeed:
    source_key: str
    seed: GaokaoSourceDocumentSeed
    status: str = "registered"


@dataclass(frozen=True)
class PathwayRuleSeed:
    pathway_code: str
    rule_code: str
    rule_name: str
    rule_type: str
    severity: str
    condition_json: dict[str, object]
    message_template: str
    source_key: str
    manual_review_required: bool = False


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
        notes_json={
            "entry": "shandong_rush_stable_safe",
            "official_boundary": "最终以官方发布和高校章程为准",
            "source_status": "2026 普通类正式招生计划和录取意见发布后需继续更新",
        },
        source_key="shandong_2025_admission_policy_reference",
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
        "shandong_2025_admission_policy_reference",
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
        "shandong_2025_admission_policy_reference",
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
        "moe_2026_special_type",
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
        "shandong_2026_spring_exam_standard",
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
        "shandong_2026_spring_exam_standard",
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
        "shandong_2026_single_comprehensive",
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
        "shandong_2026_single_comprehensive",
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
        "shandong_2026_art_policy",
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
        "shandong_2026_art_policy",
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
        "shandong_2026_sports_regular",
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
        "shandong_2026_sports_single_exam",
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
        "shandong_2026_high_level_sports",
    ),
)


D2_POLICY_SOURCE_SEEDS: tuple[PolicySourceSeed, ...] = (
    PolicySourceSeed(
        "shandong_2026_registration",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="pathway_policy",
            title="关于做好山东省2026年普通高等学校招生考试报名工作的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?BCID=20&CID=1117&NewsID=7061",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 10, 27),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于确认春季/夏季高考报名、报名条件和缴费边界。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2025_admission_policy_reference",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2025,
            source_type="pathway_policy_reference",
            title="山东省2025年普通高等学校招生录取工作的意见",
            url="https://www.sdzk.cn/NewsInfo.aspx?BCID=20&CID=1117&NewsID=6928",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 6, 18),
            parser_name="shandong_pathway_policy_reference",
            note="D2 仅作为普通类批次结构、提前批 A/B 和特殊类型批规则参考；2026 正式录取意见发布后必须替换或复核。",
        ),
        status="manual_review_required",
    ),
    PolicySourceSeed(
        "shandong_2026_subject_requirement",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="subject_requirement",
            title="2024通用版普通高校拟在山东招生专业（类）选考科目要求",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 3, 17),
            parser_name="shandong_subject_requirement",
            note="D2 路径规则用于普通类、提前批和高校专业选科要求复核。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_spring_exam_standard",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="spring_exam_category_standard",
            title="山东省春季高考统一考试招生专业类别考试标准（2026年版）",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7088",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 12, 5),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于春季高考专业类别一致性和知识/技能考试模块复核。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_single_comprehensive",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="policy",
            title="关于做好2026年高职（专科）单独考试招生和综合评价招生工作的通知",
            url="https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html",
            official_org="山东省教育厅",
            source_registry_code="sdedu",
            published_at=date(2025, 12, 22),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于单招/综评招生对象、报名、测试、专业类别和院校章程边界。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_art_policy",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="art_pathway_policy",
            title="关于印发山东省2026年普通高等学校艺术类专业招生工作实施方案的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?BCID=21&CID=1142&NewsID=7078",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 11, 24),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于艺术类别、省统考/省际联考/校考、综合分、兼报和章程复核。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_sports_regular",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="sports_pathway_policy",
            title="山东省教育厅关于做好山东省2026年普通高校体育类专业招生有关工作的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7165",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2026, 4, 1),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于体育类报名、体育专业统一测试、综合分和兼报复核。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_sports_single_exam",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="sports_single_exam_policy",
            title="关于做好2026年普通高等学校运动训练、武术与民族传统体育专业招生工作的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7120",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 12, 22),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于体育单招报名、专项报名系统、文化考试和专项考试复核。",
        ),
    ),
    PolicySourceSeed(
        "sport_2026_sports_single_exam_management",
        GaokaoSourceDocumentSeed(
            province="全国",
            year=2026,
            source_type="sports_single_exam_policy",
            title="2026年普通高等学校运动训练、武术与民族传统体育专业招生管理办法",
            url="https://www.sport.gov.cn/kjs/n23837299/c29231171/content.html",
            official_org="国家体育总局科教司",
            source_registry_code=None,
            published_at=date(2025, 11, 20),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于体育单招运动员等级、报名系统、考试和招生项目总规则复核。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_high_level_sports",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="high_level_sports_policy",
            title="关于做好2026年普通高等学校在山东省招收高水平运动队相关工作的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7121",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 12, 22),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于高水平运动队高考报名、等级证书、项目一致性和资格审查复核。",
        ),
    ),
    PolicySourceSeed(
        "moe_2026_special_type",
        GaokaoSourceDocumentSeed(
            province="全国",
            year=2026,
            source_type="special_type_policy",
            title="教育部办公厅关于做好2026年普通高等学校部分特殊类型招生工作的通知",
            url="https://www.moe.gov.cn/srcsite/A15/moe_776/tslxzs/202510/t20251031_1418664.html",
            official_org="教育部办公厅",
            source_registry_code=None,
            published_at=date(2025, 10, 17),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于特殊类型、高校专项、综合评价、高水平运动队等资格审核和信息公示边界。",
        ),
    ),
    PolicySourceSeed(
        "shandong_2026_flight_tech",
        GaokaoSourceDocumentSeed(
            province="山东",
            year=2026,
            source_type="early_batch_policy",
            title="关于做好山东省2026年普通高等学校招收民航飞行技术专业工作的通知",
            url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7069",
            official_org="山东省教育招生考试院",
            source_registry_code="sdzk",
            published_at=date(2025, 11, 11),
            parser_name="shandong_pathway_policy_reference",
            note="D2 路径规则用于提前批 A 类中飞行技术方向的年龄、体检、背景调查、语种和选科复核。",
        ),
    ),
)


D2_PATHWAY_RULE_SEEDS: tuple[PathwayRuleSeed, ...] = (
    PathwayRuleSeed(
        "summer_general_regular",
        "d2_general_gaokao_registration",
        "山东普通类高考报名确认",
        "hard_gate",
        "required",
        {"type": "boolean_is", "field": "has_gaokao_registration", "value": True},
        "学生画像需确认已完成山东 2026 普通高校招生考试报名。",
        "shandong_2026_registration",
    ),
    PathwayRuleSeed(
        "summer_general_regular",
        "d2_general_subject_combination",
        "普通类选科组合确认",
        "subject_required",
        "required",
        {"type": "field_present", "field": "subject_combination"},
        "补充学生选科组合后，才能按专业选科要求过滤候选。",
        "shandong_2026_subject_requirement",
    ),
    PathwayRuleSeed(
        "summer_general_regular",
        "d2_general_2026_plan_pending",
        "2026 正式计划待发布复核",
        "soft_warning",
        "warning",
        {"type": "manual_review", "source_status": "pending_official_release"},
        "2026 普通类正式招生计划、分数线和录取意见发布后必须重新导入并复核。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_regular",
        "d2_general_chapter_review",
        "普通类高校章程限制核验",
        "chapter_check",
        "review",
        {"type": "manual_review"},
        "正式填报前逐校核对体检、语种、单科成绩、校区和专业备注等高校章程限制。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_early_a",
        "d2_early_a_candidate_type",
        "提前批 A 类普通类身份确认",
        "hard_gate",
        "required",
        {"type": "field_in", "field": "candidate_type", "values": ["general", "普通类"]},
        "提前批 A 类需先确认学生为夏季高考普通类相关考生。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_early_a",
        "d2_early_a_physical_interview_acceptance",
        "提前批 A 类体检面试接受度",
        "hard_gate",
        "required",
        {"type": "boolean_is", "field": "accept_interview_or_physical_test", "value": True},
        "该路径通常涉及体检、面试、体能测试、政审或背景调查；学生需确认可以接受。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_early_a",
        "d2_early_a_flight_manual_review",
        "飞行技术等方向专项核验",
        "manual_check",
        "review",
        {"type": "manual_review"},
        "如关注飞行技术等提前批 A 类方向，需逐项核验年龄、性别、外语、选科、背景调查和招飞体检标准。",
        "shandong_2026_flight_tech",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "summer_general_early_b",
        "d2_early_b_candidate_type",
        "提前批 B 类普通类身份确认",
        "hard_gate",
        "required",
        {"type": "field_in", "field": "candidate_type", "values": ["general", "普通类"]},
        "提前批 B 类需先确认学生为夏季高考普通类相关考生。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_early_b",
        "d2_early_b_service_commitment",
        "定向就业或服务约束确认",
        "hard_gate",
        "required",
        {"type": "boolean_is", "field": "accept_service_commitment", "value": True},
        "公费师范生、省属公费生、定向就业等路径需学生和家庭确认可接受签约、服务年限和就业地区约束。",
        "shandong_2025_admission_policy_reference",
    ),
    PathwayRuleSeed(
        "summer_general_early_b",
        "d2_early_b_contract_manual_review",
        "提前批 B 类签约章程复核",
        "chapter_check",
        "review",
        {"type": "manual_review"},
        "需人工核对当年招生计划、签约流程、服务地限制、违约责任和高校章程。",
        "shandong_2025_admission_policy_reference",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "summer_special_type",
        "d2_special_type_score_line_review",
        "特殊类型招生控制线复核",
        "score_line",
        "required",
        {"type": "material_present", "key": "special_type_score_line_ready"},
        "补充当年特殊类型招生控制线或确认分数线后，再判断资格边界。",
        "shandong_2025_admission_policy_reference",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "summer_special_type",
        "d2_special_type_qualification",
        "特殊类型资格材料",
        "material_required",
        "required",
        {"type": "material_present", "key": "special_type_qualification"},
        "补充高校专项、资格名单、前置报名或高校测试等特殊类型资格材料。",
        "moe_2026_special_type",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "spring_exam_undergrad",
        "d2_spring_undergrad_candidate_type",
        "春季高考考生类型确认",
        "hard_gate",
        "required",
        {"type": "field_in", "field": "candidate_type", "values": ["spring_exam", "春季高考"]},
        "春季高考本科批仅适用于春季高考相关考生，不能与夏季普通类规则混用。",
        "shandong_2026_registration",
    ),
    PathwayRuleSeed(
        "spring_exam_undergrad",
        "d2_spring_undergrad_category",
        "春季高考专业类别一致",
        "category_match",
        "required",
        {"type": "field_present", "field": "spring_exam_category"},
        "补充春季高考专业类别，后续只能在对应类别内做初筛。",
        "shandong_2026_spring_exam_standard",
    ),
    PathwayRuleSeed(
        "spring_exam_junior",
        "d2_spring_junior_candidate_type",
        "春季高考专科考生类型确认",
        "hard_gate",
        "required",
        {"type": "field_in", "field": "candidate_type", "values": ["spring_exam", "春季高考"]},
        "春季高考专科批仅适用于春季高考相关考生，不能与夏季普通类规则混用。",
        "shandong_2026_registration",
    ),
    PathwayRuleSeed(
        "spring_exam_junior",
        "d2_spring_junior_category",
        "春季高考专科专业类别一致",
        "category_match",
        "required",
        {"type": "field_present", "field": "spring_exam_category"},
        "补充春季高考专业类别，后续只能在对应类别内做初筛。",
        "shandong_2026_spring_exam_standard",
    ),
    PathwayRuleSeed(
        "vocational_single_exam",
        "d2_single_registration",
        "单招高考报名确认",
        "hard_gate",
        "required",
        {"type": "boolean_is", "field": "has_gaokao_registration", "value": True},
        "高职单招考生也需确认已完成山东 2026 普通高校招生考试报名。",
        "shandong_2026_single_comprehensive",
    ),
    PathwayRuleSeed(
        "vocational_single_exam",
        "d2_single_candidate_scope",
        "单招招生对象范围",
        "hard_gate",
        "required",
        {
            "type": "any",
            "items": [
                {"type": "boolean_is", "field": "is_vocational_student", "value": True},
                {"type": "boolean_is", "field": "is_social_candidate", "value": True},
            ],
        },
        "高职单招主要面向中职应届毕业生和社会人员；需在学生画像中确认身份。",
        "shandong_2026_single_comprehensive",
    ),
    PathwayRuleSeed(
        "vocational_single_exam",
        "d2_single_social_equivalent",
        "社会人员高中阶段学历或同等学力",
        "material_required",
        "required",
        {"type": "material_present", "key": "high_school_equivalent"},
        "如学生按社会人员报考单招，需补充高中阶段毕业证书或同等学力材料。",
        "shandong_2026_single_comprehensive",
    ),
    PathwayRuleSeed(
        "vocational_single_exam",
        "d2_single_school_chapter",
        "单招院校章程和测试方式",
        "chapter_check",
        "review",
        {"type": "manual_review"},
        "逐校核对招生章程、文化素质考试、专业技能测试、退役士兵测试方式和专业类别要求。",
        "shandong_2026_single_comprehensive",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "vocational_comprehensive",
        "d2_comprehensive_candidate_scope",
        "综评普通高中应届身份",
        "hard_gate",
        "required",
        {
            "type": "all",
            "items": [
                {"type": "field_in", "field": "candidate_type", "values": ["general", "普通类"]},
                {"type": "boolean_is", "field": "is_fresh_graduate", "value": True},
            ],
        },
        "高职综合评价招生面向普通高中应届毕业生；需确认普通类身份和应届状态。",
        "shandong_2026_single_comprehensive",
    ),
    PathwayRuleSeed(
        "vocational_comprehensive",
        "d2_comprehensive_quality_record",
        "综合素质评价材料",
        "material_required",
        "required",
        {"type": "material_present", "key": "comprehensive_quality_evaluation"},
        "补充综合素质评价信息，供高职综评路径初筛和院校测试复核使用。",
        "shandong_2026_single_comprehensive",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "vocational_comprehensive",
        "d2_comprehensive_test_review",
        "综评素质测试或面试复核",
        "manual_check",
        "review",
        {"type": "manual_review"},
        "逐校核对综合评价招生章程、素质测试或面试安排、成绩组成和录取规则。",
        "shandong_2026_single_comprehensive",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "art_undergrad",
        "d2_art_undergrad_track",
        "艺术类别确认",
        "hard_gate",
        "required",
        {
            "type": "any",
            "items": [
                {"type": "field_in", "field": "candidate_type", "values": ["art", "艺术类"]},
                {"type": "field_present", "field": "art_track"},
            ],
        },
        "艺术类本科路径需先确认艺术类别或艺术方向。",
        "shandong_2026_art_policy",
    ),
    PathwayRuleSeed(
        "art_undergrad",
        "d2_art_undergrad_score",
        "艺术统考/校考成绩与文化线",
        "material_required",
        "required",
        {"type": "material_present", "key": "art_exam_score"},
        "补充艺术统考、校考或省际联考成绩，并核对对应文化控制线。",
        "shandong_2026_art_policy",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "art_junior",
        "d2_art_junior_track",
        "艺术专科类别确认",
        "hard_gate",
        "required",
        {
            "type": "any",
            "items": [
                {"type": "field_in", "field": "candidate_type", "values": ["art", "艺术类"]},
                {"type": "field_present", "field": "art_track"},
            ],
        },
        "艺术类专科路径需先确认艺术类别或艺术方向。",
        "shandong_2026_art_policy",
    ),
    PathwayRuleSeed(
        "art_junior",
        "d2_art_junior_chapter_review",
        "艺术专科录取原则和章程核验",
        "chapter_check",
        "review",
        {"type": "manual_review"},
        "艺术类不同院校录取原则、综合分、身高、色觉、单科、语种等要求差异大，必须逐校复核。",
        "shandong_2026_art_policy",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "sports_regular",
        "d2_sports_regular_track",
        "体育类身份和报名确认",
        "hard_gate",
        "required",
        {
            "type": "all",
            "items": [
                {"type": "boolean_is", "field": "has_gaokao_registration", "value": True},
                {
                    "type": "any",
                    "items": [
                        {"type": "field_in", "field": "candidate_type", "values": ["sports", "体育类"]},
                        {"type": "field_present", "field": "sports_track"},
                    ],
                },
            ],
        },
        "体育类常规批需确认已参加夏季高考报名，并选择体育类或补充体育方向。",
        "shandong_2026_sports_regular",
    ),
    PathwayRuleSeed(
        "sports_regular",
        "d2_sports_regular_score",
        "体育专业测试成绩",
        "material_required",
        "required",
        {"type": "material_present", "key": "sports_test_score"},
        "补充山东体育专业统一测试成绩，再结合综合分和批次线做初筛。",
        "shandong_2026_sports_regular",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "sports_regular",
        "d2_sports_regular_not_single_exam",
        "体育常规批与体育单招区分",
        "soft_warning",
        "warning",
        {"type": "manual_review"},
        "体育类常规批、体育单招和高水平运动队是不同路径，报名系统、测试和录取规则不能混用。",
        "shandong_2026_sports_regular",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "sports_single_exam",
        "d2_sports_single_athlete_level",
        "体育单招运动员等级",
        "material_required",
        "required",
        {"type": "material_present", "key": "athlete_level_certificate"},
        "补充运动员技术等级证书，并核对项目是否与目标院校招生项目一致。",
        "sport_2026_sports_single_exam_management",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "sports_single_exam",
        "d2_sports_single_registration_system",
        "体育单招专项报名系统",
        "time_window",
        "review",
        {"type": "manual_review"},
        "按中国运动文化教育网或体教联盟 APP 的体育单招系统完成注册、报名、缴费和考试安排核对。",
        "shandong_2026_sports_single_exam",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "high_level_sports",
        "d2_high_level_gaokao_registration",
        "高水平运动队高考报名",
        "hard_gate",
        "required",
        {"type": "boolean_is", "field": "has_gaokao_registration", "value": True},
        "高水平运动队考生必须参加山东 2026 普通高校招生考试报名。",
        "shandong_2026_high_level_sports",
    ),
    PathwayRuleSeed(
        "high_level_sports",
        "d2_high_level_athlete_level",
        "高水平运动队等级证书",
        "material_required",
        "required",
        {"type": "material_present", "key": "high_level_athlete_level"},
        "补充国家一级运动员（含）以上技术等级等材料，并核对项目一致性。",
        "shandong_2026_high_level_sports",
        manual_review_required=True,
    ),
    PathwayRuleSeed(
        "high_level_sports",
        "d2_high_level_college_qualification",
        "高水平运动队高校简章和资格审核",
        "chapter_check",
        "review",
        {"type": "manual_review"},
        "逐校核对阳光高考或高校招生网站公布的招生项目、报名条件、资格审查和专业测试要求。",
        "moe_2026_special_type",
        manual_review_required=True,
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
    source_ids = _ensure_d2_policy_source_documents(session)
    created_count = 0
    skipped_count = 0
    rule_created_count = 0
    rule_skipped_count = 0
    for seed in PATHWAY_SEEDS:
        source_id = source_ids.get(seed.source_key)
        pathway = get_pathway_by_code(session, province=DEFAULT_PROVINCE, pathway_code=seed.pathway_code)
        if pathway:
            _apply_pathway_seed(pathway, seed, source_id)
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
                source_document_id=source_id,
                summary=seed.summary,
                risk_level=seed.risk_level,
                notes_json=seed.notes_json,
            )
            session.add(pathway)
            session.flush()
            created_count += 1

        result = _ensure_baseline_rule(session, pathway, target_year, source_ids)
        rule_created_count += result[0]
        rule_skipped_count += result[1]
        result = _ensure_d2_pathway_rules(session, pathway, target_year, source_ids)
        rule_created_count += result[0]
        rule_skipped_count += result[1]

    if created_count or rule_created_count:
        write_audit_log(
            session,
            module="gaokao_pathways",
            action="bootstrap_shandong_pathways",
            target_type="gaokao_pathway",
            target_id=str(target_year),
            detail_json={
                "created_count": created_count,
                "rule_created_count": rule_created_count,
                "source_document_count": len(source_ids),
            },
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


def _ensure_d2_policy_source_documents(session: Session) -> dict[str, int]:
    source_ids: dict[str, int] = {}
    for policy_seed in D2_POLICY_SOURCE_SEEDS:
        document, _ = upsert_gaokao_source_document(session, policy_seed.seed)
        document.status = policy_seed.status
        session.flush()
        source_ids[policy_seed.source_key] = document.id
    return source_ids


def _apply_pathway_seed(
    pathway: GaokaoPathway,
    seed: PathwaySeed,
    source_document_id: int | None,
) -> None:
    pathway.pathway_name = seed.pathway_name
    pathway.pathway_group = seed.pathway_group
    pathway.student_type = seed.student_type
    pathway.exam_type = seed.exam_type
    pathway.batch_name = seed.batch_name
    pathway.volunteer_mode = seed.volunteer_mode
    pathway.max_volunteer_count = seed.max_volunteer_count
    pathway.recommendation_depth = seed.recommendation_depth
    pathway.status = "active"
    pathway.source_document_id = source_document_id
    pathway.summary = seed.summary
    pathway.risk_level = seed.risk_level
    pathway.notes_json = seed.notes_json
    pathway.is_active = True


def _ensure_d2_pathway_rules(
    session: Session,
    pathway: GaokaoPathway,
    target_year: int,
    source_ids: dict[str, int],
) -> tuple[int, int]:
    created_count = 0
    skipped_count = 0
    for seed in D2_PATHWAY_RULE_SEEDS:
        if seed.pathway_code != pathway.pathway_code:
            continue
        result = _ensure_rule_from_payload(
            session,
            pathway,
            GaokaoPathwayRulePayload(
                rule_code=seed.rule_code,
                rule_name=seed.rule_name,
                rule_type=seed.rule_type,
                severity=seed.severity,
                condition_json=seed.condition_json,
                message_template=seed.message_template,
                source_document_id=source_ids.get(seed.source_key),
                manual_review_required=seed.manual_review_required,
                valid_from_year=target_year,
            ),
        )
        created_count += result[0]
        skipped_count += result[1]
    return created_count, skipped_count


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
    source_ids: dict[str, int],
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
                source_document_id=source_ids.get("shandong_2026_registration"),
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
            source_document_id=pathway.source_document_id,
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
        if payload.source_document_id and not existing.source_document_id:
            existing.source_document_id = payload.source_document_id
        if existing.valid_from_year is None and payload.valid_from_year is not None:
            existing.valid_from_year = payload.valid_from_year
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
