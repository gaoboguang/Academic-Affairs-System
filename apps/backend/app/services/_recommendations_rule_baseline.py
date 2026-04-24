from __future__ import annotations

from app.schemas.recommendation import (
    ProvinceScoreTransformRulePayload,
    ProvinceVolunteerRulePayload,
    SubjectRequirementDictPayload,
)


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
SHANDONG_STAGE_B_NOTE = "系统基线初始化生成：基于当前山东招生计划库已出现批次整理，正式填报前仍需按当年山东省教育招生考试院公告复核。"
SHANDONG_STAGE_B_SPECIAL_RULES = [
    "山东特殊类型批次基线：已按当前招生计划库批次先行建模",
    "正式填报前需按当年山东公告复核志愿数量、投档规则和兼报限制",
]
THREE_PLUS_THREE_SUBJECTS = ["物理", "化学", "生物", "政治", "历史", "地理"]
RESELECT_SUBJECTS = ["化学", "生物", "政治", "地理"]

THREE_PLUS_THREE_SCORE_SUMMARY = "语数外原始分 + 3 门等级性考试；等级赋分表需按省份年份配置。"
THREE_PLUS_ONE_PLUS_TWO_SCORE_SUMMARY = "语数外原始分 + 首选科目原始分 + 再选 2 门等级赋分；批次与志愿结构需按省份年份复核。"
LEGACY_SCORE_SUMMARY = "旧高考文理分科兼容模式；当前仍需保留文史 / 理工逻辑，后续如省级政策调整需单独复核。"
BASELINE_RULE_SOURCE_NOTE = "系统基线初始化生成：后续需按省级公告补录正式细则。"
COMMON_RAW_SCORE_SUBJECTS = [
    ("chinese", "语文"),
    ("math", "数学"),
    ("english", "英语"),
]
THREE_PLUS_THREE_SCORE_SUBJECTS = [
    ("physics", "物理", "grade_assigned"),
    ("chemistry", "化学", "grade_assigned"),
    ("biology", "生物", "grade_assigned"),
    ("politics", "政治", "grade_assigned"),
    ("history", "历史", "grade_assigned"),
    ("geography", "地理", "grade_assigned"),
]
THREE_PLUS_ONE_PLUS_TWO_TRACK_SUBJECTS = {
    "物理类": ("physics", "物理"),
    "历史类": ("history", "历史"),
}
THREE_PLUS_ONE_PLUS_TWO_RESELECT_SCORE_SUBJECTS = [
    ("chemistry", "化学", "grade_assigned"),
    ("biology", "生物", "grade_assigned"),
    ("politics", "政治", "grade_assigned"),
    ("geography", "地理", "grade_assigned"),
]
LEGACY_TRACK_SCORE_SUBJECTS = {
    "文科": [(None, "文综", "raw")],
    "理科": [(None, "理综", "raw")],
}
THREE_PLUS_THREE_REQUIREMENT_DICT = [
    ("UNLIMITED", "不限", "no_requirement", []),
    ("PHYSICS", "物理", "require_all", ["物理"]),
    ("CHEMISTRY", "化学", "require_all", ["化学"]),
    ("BIOLOGY", "生物", "require_all", ["生物"]),
    ("POLITICS", "政治", "require_all", ["政治"]),
    ("HISTORY", "历史", "require_all", ["历史"]),
    ("GEOGRAPHY", "地理", "require_all", ["地理"]),
    ("PHYSICS_CHEMISTRY", "物理+化学", "require_all", ["物理", "化学"]),
    ("CHEMISTRY_BIOLOGY", "化学+生物", "require_all", ["化学", "生物"]),
]
THREE_PLUS_ONE_PLUS_TWO_REQUIREMENT_DICT = {
    "物理类": [
        ("UNLIMITED", "不限", "no_requirement", []),
        ("PHYSICS", "物理", "require_all", ["物理"]),
        ("PHYSICS_CHEMISTRY", "物理+化学", "require_all", ["物理", "化学"]),
        ("PHYSICS_BIOLOGY", "物理+生物", "require_all", ["物理", "生物"]),
        ("PHYSICS_CHEMISTRY_BIOLOGY", "物理+化学+生物", "require_all", ["物理", "化学", "生物"]),
    ],
    "历史类": [
        ("UNLIMITED", "不限", "no_requirement", []),
        ("HISTORY", "历史", "require_all", ["历史"]),
        ("HISTORY_POLITICS", "历史+政治", "require_all", ["历史", "政治"]),
        ("HISTORY_GEOGRAPHY", "历史+地理", "require_all", ["历史", "地理"]),
        ("HISTORY_POLITICS_GEOGRAPHY", "历史+政治+地理", "require_all", ["历史", "政治", "地理"]),
    ],
}
LEGACY_REQUIREMENT_DICT = {
    "文科": [
        ("LIBERAL_ARTS", "文科", "track_only", ["文科"]),
        ("UNLIMITED", "不限", "no_requirement", []),
    ],
    "理科": [
        ("SCIENCE", "理科", "track_only", ["理科"]),
        ("UNLIMITED", "不限", "no_requirement", []),
    ],
}


def build_province_volunteer_rule_baselines(year: int) -> list[ProvinceVolunteerRulePayload]:
    payloads: list[ProvinceVolunteerRulePayload] = []
    for province in THREE_PLUS_THREE_PROVINCES:
        payloads.append(_build_three_plus_three_payload(province, year))
    for province in THREE_PLUS_ONE_PLUS_TWO_PROVINCES:
        payloads.extend(_build_three_plus_one_plus_two_payloads(province, year))
    for province in LEGACY_PROVINCES:
        payloads.extend(_build_legacy_payloads(province, year))
    payloads.extend(_build_shandong_stage_b_payloads(year))
    return payloads


def build_province_score_transform_rule_baselines(year: int) -> list[ProvinceScoreTransformRulePayload]:
    payloads: list[ProvinceScoreTransformRulePayload] = []
    for province in THREE_PLUS_THREE_PROVINCES:
        payloads.extend(_build_three_plus_three_score_transform_payloads(province, year))
    for province in THREE_PLUS_ONE_PLUS_TWO_PROVINCES:
        payloads.extend(_build_three_plus_one_plus_two_score_transform_payloads(province, year))
    for province in LEGACY_PROVINCES:
        payloads.extend(_build_legacy_score_transform_payloads(province, year))
    return payloads


def build_subject_requirement_dict_baselines(year: int) -> list[SubjectRequirementDictPayload]:
    payloads: list[SubjectRequirementDictPayload] = []
    for province in THREE_PLUS_THREE_PROVINCES:
        payloads.extend(_build_three_plus_three_subject_requirement_payloads(province, year))
    for province in THREE_PLUS_ONE_PLUS_TWO_PROVINCES:
        payloads.extend(_build_three_plus_one_plus_two_subject_requirement_payloads(province, year))
    for province in LEGACY_PROVINCES:
        payloads.extend(_build_legacy_subject_requirement_payloads(province, year))
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


def _build_shandong_stage_b_payloads(year: int) -> list[ProvinceVolunteerRulePayload]:
    rows = [
        ("general", "常规批", 1, 96, "专业", "major_parallel", None, "山东普通类常规批实行以“专业（专业类）+学校”为单位的平行志愿；当前按 96 个志愿基线建模。"),
        ("general", "常规批（本科）", 2, 96, "专业", "major_parallel", None, "山东普通类常规批本科计划口径，按专业平行志愿基线解释。"),
        ("general", "提前批", 3, 1, "院校", "ordered_sequential", None, "山东普通类提前批规则差异较大，当前先按院校志愿和人工复核口径建模。"),
        ("general", "提前批（专科）", 4, 1, "院校", "ordered_sequential", None, "山东普通类专科提前批当前先按院校志愿和人工复核口径建模。"),
        ("general", "提前批A类（本科）", 5, 1, "院校", "ordered_sequential", None, "山东普通类提前批 A 类当前先按院校志愿和人工复核口径建模。"),
        ("general", "专科批", 6, 96, "专业", "major_parallel", None, "山东普通类专科计划当前按专业平行志愿基线解释。"),
        ("general", "特殊类型批", 7, 1, "院校", "ordered_sequential", None, "山东特殊类型批需逐项核对资格和公告，当前先按院校志愿人工复核口径建模。"),
        ("general", "3+2专本贯通培养批", 8, 96, "专业", "major_parallel", None, "山东 3+2 专本贯通培养批当前按专业平行志愿基线解释。"),
        ("general", "高职院校专项计划批", 9, 96, "专业", "major_parallel", None, "山东高职院校专项计划批当前按专业平行志愿基线解释，资格限制需人工复核。"),
        ("spring_exam", "本科批", 20, 96, "专业", "major_parallel", None, "山东春季高考本科批当前按专业平行志愿基线解释。"),
        ("spring_exam", "春季高考本科批", 21, 96, "专业", "major_parallel", None, "山东春季高考本科批当前按专业平行志愿基线解释。"),
        ("spring_exam", "本科提前批", 22, 1, "院校", "ordered_sequential", None, "山东春季高考本科提前批当前先按院校志愿人工复核口径建模。"),
        ("spring_exam", "专科批", 23, 96, "专业", "major_parallel", None, "山东春季高考专科批当前按专业平行志愿基线解释。"),
        ("spring_exam", "春季高考专科批", 24, 96, "专业", "major_parallel", None, "山东春季高考专科批当前按专业平行志愿基线解释。"),
        ("spring_exam", "高职院校专项计划批", 25, 96, "专业", "major_parallel", None, "山东春季高考高职院校专项计划批当前按专业平行志愿基线解释，资格限制需人工复核。"),
        ("spring_exam", "3+4转段春季高考批", 26, 1, "院校", "ordered_sequential", None, "山东 3+4 转段春季高考批当前先按转段资格和人工复核口径建模。"),
        ("art", "本科批", 30, 60, "专业", "major_parallel", None, "山东艺术类本科批当前按专业平行志愿基线解释，统考/校考和专业限制需人工复核。"),
        ("art", "艺术类本科批统考", 31, 60, "专业", "major_parallel", None, "山东艺术类本科批统考当前按专业平行志愿基线解释，统考类别需人工复核。"),
        ("art", "专科批", 32, 60, "专业", "major_parallel", None, "山东艺术类专科批当前按专业平行志愿基线解释。"),
        ("art", "艺术类专科批", 33, 60, "专业", "major_parallel", None, "山东艺术类专科批当前按专业平行志愿基线解释。"),
        ("art", "常规批", 34, 60, "专业", "major_parallel", None, "山东艺术类常规批当前按专业平行志愿基线解释，类别限制需人工复核。"),
        ("sports", "常规批", 40, 60, "专业", "major_parallel", None, "山东体育类常规批当前按专业平行志愿基线解释，综合分和专业测试口径需人工复核。"),
        ("sports", "常规批（本科）", 41, 60, "专业", "major_parallel", None, "山东体育类常规批本科计划当前按专业平行志愿基线解释。"),
        ("independent_recruitment", "专科批", 50, 1, "院校", "ordered_sequential", None, "山东单独招生专科批当前先按院校志愿和资格复核口径建模。"),
        ("comprehensive_evaluation", "专科批", 60, 1, "院校", "ordered_sequential", None, "山东综合评价招生专科批当前先按院校志愿和综合评价资格复核口径建模。"),
    ]
    return [
        _build_shandong_stage_b_payload(
            year=year,
            candidate_type=candidate_type,
            batch=batch,
            batch_order=batch_order,
            volunteer_limit=volunteer_limit,
            volunteer_unit_type=volunteer_unit_type,
            parallel_rule_mode=parallel_rule_mode,
            max_major_per_unit=max_major_per_unit,
            score_rule_summary=score_rule_summary,
        )
        for (
            candidate_type,
            batch,
            batch_order,
            volunteer_limit,
            volunteer_unit_type,
            parallel_rule_mode,
            max_major_per_unit,
            score_rule_summary,
        ) in rows
    ]


def _build_shandong_stage_b_payload(
    *,
    year: int,
    candidate_type: str,
    batch: str,
    batch_order: int,
    volunteer_limit: int,
    volunteer_unit_type: str,
    parallel_rule_mode: str,
    max_major_per_unit: int | None,
    score_rule_summary: str,
) -> ProvinceVolunteerRulePayload:
    return ProvinceVolunteerRulePayload(
        province="山东",
        year=year,
        exam_mode="春季高考" if candidate_type == "spring_exam" else "3+3",
        batch=batch,
        candidate_type=candidate_type,
        batch_order=batch_order,
        total_score=750,
        volunteer_limit=volunteer_limit,
        volunteer_unit_type=volunteer_unit_type,
        subject_requirement_mode="unified_subject_requirement",
        required_subjects_json=list(THREE_PLUS_THREE_SUBJECTS),
        first_choice_subjects_json=[],
        reselect_subjects_json=[],
        score_rule_summary=score_rule_summary,
        parallel_rule_mode=parallel_rule_mode,
        max_major_per_unit=max_major_per_unit,
        is_parallel=parallel_rule_mode != "ordered_sequential",
        allow_adjustment=True,
        support_collect_round=True,
        special_rules_json=list(SHANDONG_STAGE_B_SPECIAL_RULES),
        note=SHANDONG_STAGE_B_NOTE,
        is_active=True,
    )


def _build_three_plus_three_score_transform_payloads(
    province: str,
    year: int,
) -> list[ProvinceScoreTransformRulePayload]:
    payloads: list[ProvinceScoreTransformRulePayload] = []
    sort_order = 1
    for subject_code, subject_name in COMMON_RAW_SCORE_SUBJECTS:
        payloads.append(
            _build_score_transform_payload(
                province=province,
                year=year,
                exam_mode="3+3",
                subject_code=subject_code,
                subject_name=subject_name,
                score_mode="raw",
                sort_order=sort_order,
            )
        )
        sort_order += 1
    for subject_code, subject_name, score_mode in THREE_PLUS_THREE_SCORE_SUBJECTS:
        payloads.append(
            _build_score_transform_payload(
                province=province,
                year=year,
                exam_mode="3+3",
                subject_code=subject_code,
                subject_name=subject_name,
                score_mode=score_mode,
                sort_order=sort_order,
            )
        )
        sort_order += 1
    return payloads


def _build_three_plus_one_plus_two_score_transform_payloads(
    province: str,
    year: int,
) -> list[ProvinceScoreTransformRulePayload]:
    payloads: list[ProvinceScoreTransformRulePayload] = []
    for exam_mode, (first_choice_code, first_choice_name) in THREE_PLUS_ONE_PLUS_TWO_TRACK_SUBJECTS.items():
        sort_order = 1
        for subject_code, subject_name in COMMON_RAW_SCORE_SUBJECTS:
            payloads.append(
                _build_score_transform_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    subject_code=subject_code,
                    subject_name=subject_name,
                    score_mode="raw",
                    sort_order=sort_order,
                )
            )
            sort_order += 1
        payloads.append(
            _build_score_transform_payload(
                province=province,
                year=year,
                exam_mode=exam_mode,
                subject_code=first_choice_code,
                subject_name=first_choice_name,
                score_mode="raw",
                sort_order=sort_order,
            )
        )
        sort_order += 1
        for subject_code, subject_name, score_mode in THREE_PLUS_ONE_PLUS_TWO_RESELECT_SCORE_SUBJECTS:
            payloads.append(
                _build_score_transform_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    subject_code=subject_code,
                    subject_name=subject_name,
                    score_mode=score_mode,
                    sort_order=sort_order,
                )
            )
            sort_order += 1
    return payloads


def _build_legacy_score_transform_payloads(
    province: str,
    year: int,
) -> list[ProvinceScoreTransformRulePayload]:
    payloads: list[ProvinceScoreTransformRulePayload] = []
    for exam_mode, track_subjects in LEGACY_TRACK_SCORE_SUBJECTS.items():
        sort_order = 1
        for subject_code, subject_name in COMMON_RAW_SCORE_SUBJECTS:
            payloads.append(
                _build_score_transform_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    subject_code=subject_code,
                    subject_name=subject_name,
                    score_mode="raw",
                    sort_order=sort_order,
                )
            )
            sort_order += 1
        for subject_code, subject_name, score_mode in track_subjects:
            payloads.append(
                _build_score_transform_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    subject_code=subject_code,
                    subject_name=subject_name,
                    score_mode=score_mode,
                    sort_order=sort_order,
                )
            )
            sort_order += 1
    return payloads


def _build_score_transform_payload(
    *,
    province: str,
    year: int,
    exam_mode: str,
    subject_code: str | None,
    subject_name: str,
    score_mode: str,
    sort_order: int,
) -> ProvinceScoreTransformRulePayload:
    grade_table_json: list[dict[str, object]] = []
    formula_json: dict[str, object] = {}
    source_note = BASELINE_RULE_SOURCE_NOTE
    note = "系统基线初始化生成：后续需按省级公告补录正式赋分区间或换算公式。"
    if score_mode == "grade_assigned":
        grade_table_json = [{"grade": "待补录", "summary": "需补录正式等级赋分表"}]
        formula_json = {"mode": "grade_assigned", "status": "baseline_pending"}
    else:
        formula_json = {"mode": "raw"}

    return ProvinceScoreTransformRulePayload(
        province=province,
        year=year,
        exam_mode=exam_mode,
        subject_code=subject_code,
        subject_name=subject_name,
        score_mode=score_mode,
        sort_order=sort_order,
        grade_table_json=grade_table_json,
        formula_json=formula_json,
        source_note=source_note,
        note=note,
        is_active=True,
    )


def _build_three_plus_three_subject_requirement_payloads(
    province: str,
    year: int,
) -> list[SubjectRequirementDictPayload]:
    return [
        _build_subject_requirement_payload(
            province=province,
            year=year,
            exam_mode="3+3",
            requirement_code=requirement_code,
            requirement_text=requirement_text,
            match_mode=match_mode,
            normalized_subjects=normalized_subjects,
            sort_order=index,
        )
        for index, (requirement_code, requirement_text, match_mode, normalized_subjects) in enumerate(
            THREE_PLUS_THREE_REQUIREMENT_DICT,
            start=1,
        )
    ]


def _build_three_plus_one_plus_two_subject_requirement_payloads(
    province: str,
    year: int,
) -> list[SubjectRequirementDictPayload]:
    payloads: list[SubjectRequirementDictPayload] = []
    for exam_mode, rows in THREE_PLUS_ONE_PLUS_TWO_REQUIREMENT_DICT.items():
        payloads.extend(
            [
                _build_subject_requirement_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    requirement_code=requirement_code,
                    requirement_text=requirement_text,
                    match_mode=match_mode,
                    normalized_subjects=normalized_subjects,
                    sort_order=index,
                )
                for index, (requirement_code, requirement_text, match_mode, normalized_subjects) in enumerate(
                    rows,
                    start=1,
                )
            ]
        )
    return payloads


def _build_legacy_subject_requirement_payloads(
    province: str,
    year: int,
) -> list[SubjectRequirementDictPayload]:
    payloads: list[SubjectRequirementDictPayload] = []
    for exam_mode, rows in LEGACY_REQUIREMENT_DICT.items():
        payloads.extend(
            [
                _build_subject_requirement_payload(
                    province=province,
                    year=year,
                    exam_mode=exam_mode,
                    requirement_code=requirement_code,
                    requirement_text=requirement_text,
                    match_mode=match_mode,
                    normalized_subjects=normalized_subjects,
                    sort_order=index,
                )
                for index, (requirement_code, requirement_text, match_mode, normalized_subjects) in enumerate(
                    rows,
                    start=1,
                )
            ]
        )
    return payloads


def _build_subject_requirement_payload(
    *,
    province: str,
    year: int,
    exam_mode: str,
    requirement_code: str,
    requirement_text: str,
    match_mode: str,
    normalized_subjects: list[str],
    sort_order: int,
) -> SubjectRequirementDictPayload:
    return SubjectRequirementDictPayload(
        province=province,
        year=year,
        exam_mode=exam_mode,
        requirement_code=requirement_code,
        requirement_text=requirement_text,
        match_mode=match_mode,
        sort_order=sort_order,
        normalized_subjects_json=list(normalized_subjects),
        source_note=BASELINE_RULE_SOURCE_NOTE,
        note="系统基线初始化生成：当前仅提供第一轮语义编码，需按省级公告补录完整选科表达。",
        is_active=True,
    )
