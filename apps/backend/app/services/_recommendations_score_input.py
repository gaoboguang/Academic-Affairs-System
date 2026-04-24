from __future__ import annotations

from fastapi import HTTPException


def resolve_score_input_context(
    *,
    score_input_mode: str | None,
    student_rank_override: int | None,
    comprehensive_score: float | None,
    culture_score: float | None,
    score_range_min: float | None,
    score_range_max: float | None,
    rank_range_min: int | None,
    rank_range_max: int | None,
    reference_exam_name: str | None,
    use_historical_mapping: bool,
    risk_preference: str | None,
    total_score: float,
    snapshot_rank: int | None,
) -> dict[str, object]:
    mode = (score_input_mode or "actual_rank").strip() or "actual_rank"
    score_value, score_source = _resolve_score_value(
        comprehensive_score=comprehensive_score,
        culture_score=culture_score,
        total_score=total_score,
    )
    effective_rank = student_rank_override or snapshot_rank
    notes: list[str] = []
    confidence = "official"
    normalized_reference_exam_name = (reference_exam_name or "").strip() or None

    if mode == "actual_rank":
        if student_rank_override:
            notes.append(f"当前按手工位次 {student_rank_override} 覆盖考试位次。")
        else:
            notes.append("当前按考试正式位次刷新候选池。")
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": effective_rank,
            "score_value": score_value,
            "mode_label": "正式位次",
            "confidence": confidence,
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    if mode == "actual_score":
        notes.append("当前按正式分数模式生成，不直接使用正式位次。")
        if use_historical_mapping:
            notes.append("已标记为结合历年分数-位次映射人工复核。")
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": None,
            "score_value": score_value,
            "mode_label": "正式分数",
            "confidence": "score_only",
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    if mode == "estimated_score":
        if comprehensive_score is None and culture_score is None:
            raise HTTPException(status_code=400, detail="预估分模式至少需要填写预估总分或文化分")
        notes.append(f"当前按预估分 {score_value} 模拟。")
        if use_historical_mapping:
            notes.append("结果基于历史映射假设，正式出分后建议重新计算。")
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": None,
            "score_value": score_value,
            "mode_label": "预估分数",
            "confidence": "estimated",
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    if mode == "estimated_score_and_rank":
        if student_rank_override is None:
            raise HTTPException(status_code=400, detail="预估分+位次模式需要填写预估位次")
        if comprehensive_score is None and culture_score is None:
            raise HTTPException(status_code=400, detail="预估分+位次模式需要填写预估分数")
        notes.append("当前按预估位次为主、预估分数为辅的模拟模式生成。")
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": student_rank_override,
            "score_value": score_value,
            "mode_label": "预估分数 + 预估位次",
            "confidence": "estimated",
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    if mode == "score_range":
        if score_range_min is None or score_range_max is None:
            raise HTTPException(status_code=400, detail="分数区间模式需要填写上下限")
        if score_range_min > score_range_max:
            raise HTTPException(status_code=400, detail="分数区间下限不能大于上限")
        selected_score = _pick_range_value(
            float(score_range_min),
            float(score_range_max),
            risk_preference,
            reverse=False,
        )
        notes.append(
            f"当前按 {score_range_min}-{score_range_max} 分区间模拟，已按{_risk_preference_label(risk_preference)}取值。"
        )
        if use_historical_mapping:
            notes.append("结果已标记为历史映射估算，正式出分后建议重新计算。")
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": None,
            "score_value": selected_score,
            "mode_label": "分数区间",
            "confidence": "range_estimated",
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    if mode == "rank_range":
        if rank_range_min is None or rank_range_max is None:
            raise HTTPException(status_code=400, detail="位次区间模式需要填写上下限")
        if rank_range_min > rank_range_max:
            raise HTTPException(status_code=400, detail="位次区间下限不能大于上限")
        selected_rank = round(
            _pick_range_value(
                float(rank_range_min),
                float(rank_range_max),
                risk_preference,
                reverse=True,
            )
        )
        notes.append(
            f"当前按 {rank_range_min}-{rank_range_max} 位次区间模拟，已按{_risk_preference_label(risk_preference)}取值。"
        )
        if normalized_reference_exam_name:
            notes.append(f"参考考试：{normalized_reference_exam_name}。")
        return {
            "effective_rank": selected_rank,
            "score_value": score_value,
            "mode_label": "位次区间",
            "confidence": "range_estimated",
            "reference_exam_name": normalized_reference_exam_name,
            "use_historical_mapping": use_historical_mapping,
            "score_source": score_source,
            "notes": notes,
        }

    raise HTTPException(status_code=400, detail="暂不支持的分数输入模式")


def apply_input_context_to_evaluation(evaluation: dict[str, object], input_context: dict[str, object]) -> None:
    notes = [str(item).strip() for item in input_context.get("notes") or [] if str(item).strip()]
    if notes:
        evaluation["reason_text"] = f"{evaluation['reason_text']} {' '.join(notes)}"
    risk_flags = list(evaluation.get("risk_flags_json") or [])
    confidence = str(input_context.get("confidence") or "")
    if confidence in {"estimated", "range_estimated"}:
        risk_flags.append("simulation_mode")
    if confidence in {"score_only", "estimated", "range_estimated"}:
        risk_flags.append("manual_formula_check")
    evaluation["risk_flags_json"] = sorted(set(risk_flags))
    snapshot_json = dict(evaluation.get("snapshot_json") or {})
    snapshot_json.update(
        {
            "score_input_label": input_context.get("mode_label"),
            "score_confidence": input_context.get("confidence"),
            "reference_exam_name": input_context.get("reference_exam_name"),
            "use_historical_mapping": input_context.get("use_historical_mapping"),
            "score_source": input_context.get("score_source"),
            "input_notes": notes,
        }
    )
    evaluation["snapshot_json"] = snapshot_json


def _first_defined(*values: float | None) -> float | None:
    for value in values:
        if value is not None:
            return value
    return None


def _resolve_score_value(
    *,
    comprehensive_score: float | None,
    culture_score: float | None,
    total_score: float,
) -> tuple[float | None, str]:
    if comprehensive_score is not None:
        return comprehensive_score, "comprehensive_score"
    if culture_score is not None:
        return culture_score, "culture_score"
    return total_score, "total_score"


def _pick_range_value(lower: float, upper: float, risk_preference: str | None, *, reverse: bool) -> float:
    preference = (risk_preference or "balanced").strip() or "balanced"
    if preference == "conservative":
        return upper if reverse else lower
    if preference == "aggressive":
        return lower if reverse else upper
    return round((lower + upper) / 2, 2)


def _risk_preference_label(risk_preference: str | None) -> str:
    labels = {
        "conservative": "保守偏好",
        "balanced": "平衡偏好",
        "aggressive": "激进偏好",
    }
    return labels.get((risk_preference or "balanced").strip(), "平衡偏好")
