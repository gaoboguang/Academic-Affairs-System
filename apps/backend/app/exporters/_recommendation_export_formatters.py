from __future__ import annotations

from datetime import datetime


RECOMMENDATION_RISK_FLAG_LABELS = {
    "sample_insufficient": "样本不足",
    "rank_missing": "缺少位次，分数参考",
    "rank_projection_from_previous_year": "按上一年一分一段估算位次",
    "rank_projection_from_school_exam": "校内考试估算位次",
    "historical_data_missing": "历史样本不足",
    "three_year_data_incomplete": "近三年样本不完整",
    "plan_missing": "目标年份招生计划暂缺",
    "plan_decreased": "招生计划减少",
    "subject_requirement_mismatch": "选科要求不符",
    "subject_requirement_check": "需复核选科要求",
    "special_requirement_detected": "存在专业特殊要求",
    "not_enough_safety_choices": "保底数量不足",
    "general_reference_fallback": "缺少专门录取结果，按普通类参考",
    "score_line_reference_only": "缺少专门录取结果，按省控线初筛",
    "score_line_only_reference": "仅按省控线参考",
    "cross_year_score_line_reference": "省控线按跨年份参考",
    "plan_only_reference": "缺少专门结果，仅按计划清单初筛",
    "chapter_pending_review": "章程待补链",
    "chapter_special_requirement": "章程限制已提取",
    "art_recommendation": "艺体推荐",
    "track_unconfirmed": "艺体方向待确认",
    "manual_formula_check": "需人工核对招生章程",
    "whitelist_override": "白名单放宽",
    "career_mapping_pending": "职业路径映射待维护",
    "postgraduate_path_mismatch": "与读研接受度不匹配",
    "certificate_path_mismatch": "与资格证接受度不匹配",
    "long_training_path_mismatch": "与长培养周期接受度不匹配",
    "public_service_path_mismatch": "与考公考编接受度不匹配",
    "major_baseline_missing": "专业线缺失，按院校线参考",
    "subject_requirement_check": "需复核选科要求",
    "simulation_mode": "模拟测算",
}

SHANDONG_2026_DATA_NOTICE = (
    "2026 普通类正式招生计划如未完全公开，当前主要参考 2023-2025 历史投档数据；"
    "正式填报前需导入 2026 官方计划，并以山东省教育招生考试院最终发布的招生计划和高校章程为准。"
)

RECOMMENDATION_GLOBAL_RISK_NOTICES = [
    "普通类推荐主要基于已导入的历史录取、招生计划和位次口径，可作为当前主链路参考。",
    "单招、综评、艺术、体育、春考等特殊类型如缺专门录取结果，只能做资格或方向初筛，不能视作完整录取把握。",
    "2024 招生计划数量偏少时，需要核验官方完整性后再定稿。",
    "2026 正式招生计划、一分一段和省控线需等待官方发布，正式填报前必须替换为当年官方数据。",
    "招生章程限制链仍需人工复核，尤其是选科、体检、单科、语种、校区和培养模式要求。",
]


def read_nested_number(value: object, key: str) -> object:
    if isinstance(value, dict):
        return value.get(key)
    return None


def format_export_value(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def format_percent_value(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.1f}%"
    return "-"


def format_years(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "-"
    return " / ".join(str(item) for item in value if item is not None) or "-"


def format_source_document_ids(value: object) -> str:
    if not isinstance(value, list) or not value:
        return "-"
    return " / ".join(str(item) for item in value if item is not None) or "-"


def format_shandong_bucket(value: object) -> str:
    mapping = {"rush": "冲", "stable": "稳", "safe": "保", "watch": "仅关注"}
    return mapping.get(str(value), str(value or "-"))


def format_shandong_student_type(value: object) -> str:
    mapping = {"general": "普通类"}
    return mapping.get(str(value), str(value or "-"))


def format_shandong_source_mode(value: object) -> str:
    mapping = {
        "projection": "学生考试估算",
        "exam_projection": "学生考试估算",
        "manual_score": "手动预估分",
        "manual_rank": "手动全省位次",
    }
    return mapping.get(str(value), str(value or "-"))


def format_shandong_rank_basis(value: object) -> str:
    mapping = {
        "manual_rank": "手动填写全省位次",
        "manual_score": "按一分一段由分数换算",
        "previous_year_score_rank_segment": "按上一年一分一段临时换算",
        "exam_projection": "按校内考试估算",
    }
    return mapping.get(str(value), str(value or "-"))


def format_shandong_risk_preference(value: object) -> str:
    mapping = {"conservative": "保守", "balanced": "均衡", "aggressive": "冲刺"}
    return mapping.get(str(value), str(value or "-"))


def format_shandong_confidence(value: object) -> str:
    mapping = {"high": "高", "medium": "中", "low": "低"}
    return mapping.get(str(value), str(value or "-"))


def format_shandong_rank_range(payload: dict[str, object]) -> str:
    low = payload.get("rank_range_low")
    high = payload.get("rank_range_high")
    if low is None and high is None:
        return "-"
    if low == high:
        return str(low)
    return f"{format_export_value(low)} - {format_export_value(high)}"


def read_snapshot_value(row: dict[str, object], key: str) -> object:
    snapshot = row.get("snapshot_json")
    if isinstance(snapshot, dict):
        return snapshot.get(key)
    return None


def format_parallel_rule_mode(mode: object, is_parallel: object) -> str:
    mapping = {
        "college_major_parallel": "院校 + 专业平行",
        "group_parallel": "院校专业组平行",
        "major_parallel": "专业平行",
        "ordered_sequential": "顺序志愿",
    }
    if isinstance(mode, str) and mode.strip():
        return mapping.get(mode, mode)
    return "平行志愿" if bool(is_parallel) else "未设"


def format_subject_requirement_mode(mode: object) -> str:
    mapping = {
        "unified_subject_requirement": "统一选科要求",
        "first_choice_reselect": "首选 + 再选",
        "major_level_requirement": "专业级选科要求",
    }
    if isinstance(mode, str) and mode.strip():
        return mapping.get(mode, mode)
    return "未设"


def format_signed_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    if value < 0:
        return str(value)
    return "0"


def format_compare_scheme_generated_date(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        current = value.strip()
        if not current:
            return None
        return current[:10]
    return None


def read_recommendation_snapshot_number(item: dict[str, object], key: str) -> float | None:
    snapshot = item.get("snapshot_json")
    if not isinstance(snapshot, dict):
        return None
    return read_recommendation_metric_number(snapshot.get(key))


def read_recommendation_metric_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None
