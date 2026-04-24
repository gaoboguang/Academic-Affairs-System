from __future__ import annotations

from dataclasses import dataclass

from app.models import EnrollmentPlan

from ._recommendations_special_type_rules import SpecialTypeContext, build_special_type_context


@dataclass
class FallbackPriority:
    score: float
    label: str
    notes: list[str]
    category_label: str | None = None
    review_notes: list[str] | None = None


def build_fallback_priority(
    *,
    plan: EnrollmentPlan,
    reference_scope: str | None,
    student_type: str,
    score_value: float | None = None,
    reference_score: float | None = None,
    career_match_score: float | None = None,
    batch_order: int | None = None,
    batch_dict_sort_order: int | None = None,
    has_chapter_url: bool = False,
    chapter_review_status: str | None = None,
    has_chapter_restrictions: bool = False,
    special_type_context: SpecialTypeContext | None = None,
) -> FallbackPriority | None:
    if reference_scope not in {"score_line", "plan_only"}:
        return None

    score = 0.0
    notes: list[str] = []
    special_context = special_type_context or build_special_type_context(plan=plan, student_type=student_type)
    review_notes = list(special_context.review_notes)
    category_label = special_context.category_label
    if category_label:
        score += special_context.priority_bonus
        if special_context.priority_bonus > 0:
            notes.append(f"已识别细分类别：{category_label}")
        else:
            notes.append(f"细分类别待人工复核：{category_label}")
    notes.extend(special_context.priority_notes)

    if reference_scope == "score_line":
        score += 18
        notes.append("有省级控制线，可先判断资格线是否过线")
        if score_value is not None and reference_score is not None:
            margin = round(float(score_value) - float(reference_score), 2)
            if margin >= 60:
                score += 16
                notes.append(f"高出省控线 {margin:g} 分，资格初筛余量较大")
            elif margin >= 30:
                score += 10
                notes.append(f"高出省控线 {margin:g} 分，资格初筛有一定余量")
            elif margin >= 0:
                score += 4
                notes.append(f"刚过省控线 {margin:g} 分，需谨慎核对专业规则")
    else:
        score += 8
        notes.append("仅按当年招生计划初筛，需后续补录取结果")
        if student_type == "spring_exam":
            score += 6
            notes.append("春季高考需优先核对专业类别和技能考试类别")
        elif student_type == "comprehensive_evaluation":
            score += 5
            notes.append("综合评价需优先核对高校测试和折算规则")
        elif student_type == "independent_recruitment":
            score += 4
            notes.append("单独招生需优先核对报名、校测和职业适应性测试条件")

    order_value = batch_order if batch_order is not None else batch_dict_sort_order
    if order_value is not None:
        if order_value <= 2:
            score += 18
            notes.append("批次顺序靠前，适合优先核看")
        elif order_value <= 5:
            score += 12
            notes.append("批次顺序处于主要批次范围")
        else:
            score += 6
            notes.append("批次顺序靠后，适合补充关注")

    plan_count = int(plan.plan_count or 0)
    if plan_count >= 30:
        score += 18
        notes.append(f"计划数 {plan_count}，容量相对更高")
    elif plan_count >= 15:
        score += 12
        notes.append(f"计划数 {plan_count}，有一定容量")
    elif plan_count > 0:
        score += 6
        notes.append(f"计划数 {plan_count}，容量偏小需慎比")

    college = plan.college
    level_text = " ".join(
        segment
        for segment in [
            college.school_type if college else None,
            " ".join(college.school_level_tags_json or []) if college else None,
        ]
        if segment
    )
    if any(keyword in level_text for keyword in ("双一流", "985", "211")):
        score += 12
        notes.append("院校层次标签较高")
    elif "本科" in level_text:
        score += 7
        notes.append("本科层次计划")
    elif "公办" in level_text:
        score += 5
        notes.append("公办院校计划")

    if career_match_score is not None:
        if career_match_score >= 50:
            score += 18
            notes.append("职业方向匹配较强")
        elif career_match_score >= 30:
            score += 12
            notes.append("职业方向有一定匹配")
        elif career_match_score > 0:
            score += 6
            notes.append("职业方向有弱匹配")

    if has_chapter_url:
        score += 4
        notes.append("招生章程链路已接入")
    elif chapter_review_status:
        score -= 4
        notes.append("招生章程仍待补链")
    elif student_type in {"comprehensive_evaluation", "independent_recruitment"}:
        score -= 6
        notes.append("综评/单招高度依赖学校章程，当前章程链路待补")

    if has_chapter_restrictions:
        score -= 6
        notes.append("章程限制字段已提取，正式填报需逐条复核")
    if plan.subject_requirement:
        review_notes.append(f"核对选科或专业要求：{plan.subject_requirement}")
    if plan.tuition_fee:
        review_notes.append(f"核对学费：{plan.tuition_fee}")
    if plan.training_location:
        review_notes.append(f"核对培养地点：{plan.training_location}")

    normalized_score = round(max(min(score, 100.0), 0.0), 2)
    if normalized_score >= 50:
        label = "优先核看"
    elif normalized_score >= 25:
        label = "重点比较"
    else:
        label = "补充关注"

    return FallbackPriority(
        score=normalized_score,
        label=label,
        notes=_dedupe_notes(notes),
        category_label=category_label,
        review_notes=_dedupe_notes(review_notes),
    )


def _dedupe_notes(notes: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in notes:
        current = item.strip()
        if not current or current in seen:
            continue
        seen.add(current)
        result.append(current)
    return result
