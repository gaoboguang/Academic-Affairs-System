from __future__ import annotations

from app.schemas.recommendation import ProvinceVolunteerRulePayload


THREE_PLUS_THREE_PROVINCES = [
    "北京",
    "天津",
    "上海",
    "浙江",
    "山东",
    "海南",
]

THREE_PLUS_ONE_PLUS_TWO_PROVINCES = [
    "河北",
    "辽宁",
    "江苏",
    "福建",
    "湖北",
    "湖南",
    "广东",
    "重庆",
    "甘肃",
    "黑龙江",
    "吉林",
    "安徽",
    "江西",
    "贵州",
    "广西",
    "山西",
    "内蒙古",
    "河南",
    "四川",
    "云南",
    "陕西",
    "青海",
    "宁夏",
]

LEGACY_PROVINCES = [
    "西藏",
    "新疆",
]

BASELINE_BATCH = "本科批"
BASELINE_NOTE = "系统基线初始化生成：当前仅内置本科批第一版起始规则，志愿数上限、单位类型和征集志愿规则需按当年省级公告补录。"
BASELINE_SPECIAL_RULES = [
    "基线初始化：志愿数上限、征集志愿和批次结构需按当年省级公告复核",
]
THREE_PLUS_THREE_SUBJECTS = ["物理", "化学", "生物", "政治", "历史", "地理"]
RESELECT_SUBJECTS = ["化学", "生物", "政治", "地理"]

THREE_PLUS_THREE_SCORE_SUMMARY = "语数外原始分 + 3 门等级性考试；等级赋分表需按省份年份配置。"
THREE_PLUS_ONE_PLUS_TWO_SCORE_SUMMARY = "语数外原始分 + 首选科目原始分 + 再选 2 门等级赋分；批次与志愿结构需按省份年份复核。"
LEGACY_SCORE_SUMMARY = "旧高考文理分科兼容模式；当前仍需保留文史 / 理工逻辑，后续如省级政策调整需单独复核。"


def build_province_volunteer_rule_baselines(year: int) -> list[ProvinceVolunteerRulePayload]:
    payloads: list[ProvinceVolunteerRulePayload] = []
    for province in THREE_PLUS_THREE_PROVINCES:
        payloads.append(_build_three_plus_three_payload(province, year))
    for province in THREE_PLUS_ONE_PLUS_TWO_PROVINCES:
        payloads.extend(_build_three_plus_one_plus_two_payloads(province, year))
    for province in LEGACY_PROVINCES:
        payloads.extend(_build_legacy_payloads(province, year))
    return payloads


def _build_three_plus_three_payload(province: str, year: int) -> ProvinceVolunteerRulePayload:
    total_score = 750
    score_rule_summary = THREE_PLUS_THREE_SCORE_SUMMARY
    special_rules = list(BASELINE_SPECIAL_RULES)
    if province == "上海":
        total_score = 660
        score_rule_summary = "语数外原始分 + 3 门等级性考试；总分口径为 660，需按上海年份细则单独维护。"
    elif province == "海南":
        total_score = 900
        score_rule_summary = "语数外原始分 + 3 门等级性考试；总分口径为 900，必须单独建模。"
    elif province == "山东":
        score_rule_summary = "语数外原始分 + 3 门等级性考试；需同时支持计划查询与预填表能力。"
        special_rules.append("山东需继续补齐计划查询与预填表细节")

    return ProvinceVolunteerRulePayload(
        province=province,
        year=year,
        exam_mode="3+3",
        batch=BASELINE_BATCH,
        candidate_type="",
        batch_order=1,
        total_score=total_score,
        volunteer_limit=45,
        volunteer_unit_type="专业",
        subject_requirement_mode="unified_subject_requirement",
        required_subjects_json=list(THREE_PLUS_THREE_SUBJECTS),
        first_choice_subjects_json=[],
        reselect_subjects_json=[],
        score_rule_summary=score_rule_summary,
        parallel_rule_mode="major_parallel",
        max_major_per_unit=None,
        is_parallel=True,
        allow_adjustment=True,
        support_collect_round=False,
        special_rules_json=special_rules,
        note=BASELINE_NOTE,
        is_active=True,
    )


def _build_three_plus_one_plus_two_payloads(province: str, year: int) -> list[ProvinceVolunteerRulePayload]:
    volunteer_unit_type = "专业"
    parallel_rule_mode = "major_parallel"
    max_major_per_unit = None
    score_rule_summary = THREE_PLUS_ONE_PLUS_TWO_SCORE_SUMMARY
    special_rules = list(BASELINE_SPECIAL_RULES)

    if province == "广东":
        volunteer_unit_type = "院校专业组"
        parallel_rule_mode = "group_parallel"
        max_major_per_unit = 6
        score_rule_summary = "语数外原始分 + 首选物理 / 历史原始分 + 再选 2 门等级赋分；院校专业组规则需按广东当年公告维护。"
        special_rules.append("广东需维护院校专业组与组内专业上限")
    elif province == "河南":
        score_rule_summary = "语数外原始分 + 首选物理 / 历史原始分 + 再选 2 门等级赋分；再选科目赋分细则需按河南口径维护。"

    payloads: list[ProvinceVolunteerRulePayload] = []
    for exam_mode, first_choice in [("物理类", "物理"), ("历史类", "历史")]:
        payloads.append(
            ProvinceVolunteerRulePayload(
                province=province,
                year=year,
                exam_mode=exam_mode,
                batch=BASELINE_BATCH,
                candidate_type="",
                batch_order=1,
                total_score=750,
                volunteer_limit=45,
                volunteer_unit_type=volunteer_unit_type,
                subject_requirement_mode="first_choice_reselect",
                required_subjects_json=[],
                first_choice_subjects_json=[first_choice],
                reselect_subjects_json=list(RESELECT_SUBJECTS),
                score_rule_summary=score_rule_summary,
                parallel_rule_mode=parallel_rule_mode,
                max_major_per_unit=max_major_per_unit,
                is_parallel=True,
                allow_adjustment=True,
                support_collect_round=False,
                special_rules_json=special_rules,
                note=BASELINE_NOTE,
                is_active=True,
            )
        )
    return payloads


def _build_legacy_payloads(province: str, year: int) -> list[ProvinceVolunteerRulePayload]:
    payloads: list[ProvinceVolunteerRulePayload] = []
    special_rules = list(BASELINE_SPECIAL_RULES)
    if province == "新疆":
        special_rules.append("新疆后续如切换综合改革，需按新模式重新建模")

    for exam_mode in ["文科", "理科"]:
        payloads.append(
            ProvinceVolunteerRulePayload(
                province=province,
                year=year,
                exam_mode=exam_mode,
                batch=BASELINE_BATCH,
                candidate_type="",
                batch_order=1,
                total_score=750,
                volunteer_limit=45,
                volunteer_unit_type="院校",
                subject_requirement_mode="legacy_track",
                required_subjects_json=[exam_mode],
                first_choice_subjects_json=[],
                reselect_subjects_json=[],
                score_rule_summary=LEGACY_SCORE_SUMMARY,
                parallel_rule_mode="ordered_sequential",
                max_major_per_unit=None,
                is_parallel=False,
                allow_adjustment=True,
                support_collect_round=False,
                special_rules_json=special_rules,
                note=BASELINE_NOTE,
                is_active=True,
            )
        )
    return payloads
