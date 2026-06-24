from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    KnowledgePoint,
    ScoreKnowledgeSnapshot,
    ScoreQuestion,
    ScoreQuestionKnowledgePoint,
    ScoreQuestionRecord,
    ScoreSubjectSnapshot,
    ScoreTotalSnapshot,
)
from app.services.knowledge_base import KnowledgeResolveResult

MIN_KNOWLEDGE_FULL_SCORE = 5.0


def rebuild_score_knowledge_snapshots(session: Session, exam_id: int) -> int:
    session.execute(delete(ScoreKnowledgeSnapshot).where(ScoreKnowledgeSnapshot.exam_id == exam_id))

    records = list(
        session.scalars(
            select(ScoreQuestionRecord).where(
                ScoreQuestionRecord.exam_id == exam_id,
                ScoreQuestionRecord.is_active.is_(True),
            )
        ).all()
    )
    if not records:
        return 0

    questions = {
        item.id: item
        for item in session.scalars(
            select(ScoreQuestion).where(ScoreQuestion.exam_id == exam_id, ScoreQuestion.is_active.is_(True))
        ).all()
    }
    knowledge_links_by_question: dict[int, list[ScoreQuestionKnowledgePoint]] = defaultdict(list)
    for link in session.scalars(
        select(ScoreQuestionKnowledgePoint).where(ScoreQuestionKnowledgePoint.is_active.is_(True))
    ).all():
        knowledge_links_by_question[link.question_id].append(link)

    aggregates: dict[tuple[int, int, int, int], dict[str, object]] = {}
    grade_aggregates: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: {"score": 0.0, "full_score": 0.0})
    for record in records:
        question = questions.get(record.question_id)
        if question is None:
            continue
        links = knowledge_links_by_question.get(question.id) or []
        if not links:
            continue
        active_links = [link for link in links if link.weight > 0]
        total_weight = sum(link.weight for link in active_links) or float(len(active_links))
        for link in active_links:
            weight_ratio = link.weight / total_weight
            score = (record.score or 0.0) * weight_ratio if record.score_status == "normal" else 0.0
            full_score = question.full_score * weight_ratio
            key = (record.student_id, record.subject_id, link.knowledge_point_id, exam_id)
            current = aggregates.setdefault(
                key,
                {
                    "score": 0.0,
                    "full_score": 0.0,
                    "questions": set(),
                    "error_tags": Counter(),
                },
            )
            current["score"] = float(current["score"]) + score
            current["full_score"] = float(current["full_score"]) + full_score
            current_questions = current["questions"]
            if isinstance(current_questions, set):
                current_questions.add(question.question_no)
            current_error_tags = current["error_tags"]
            if isinstance(current_error_tags, Counter):
                for tag in _extract_error_tag_names(record.error_tags_json):
                    current_error_tags[tag] += 1
            grade_key = (record.subject_id, link.knowledge_point_id)
            grade_aggregates[grade_key]["score"] += score
            grade_aggregates[grade_key]["full_score"] += full_score

    subject_weight_map = _build_subject_weight_map(session, exam_id)
    created = 0
    now = datetime.now()
    for (student_id, subject_id, knowledge_point_id, _exam_id), data in aggregates.items():
        score = round(float(data["score"]), 4)
        full_score = round(float(data["full_score"]), 4)
        if full_score <= 0:
            continue
        score_rate = round(score / full_score, 4)
        grade_full_score = grade_aggregates[(subject_id, knowledge_point_id)]["full_score"]
        grade_score = grade_aggregates[(subject_id, knowledge_point_id)]["score"]
        grade_average_rate = round(grade_score / grade_full_score, 4) if grade_full_score > 0 else None
        grade_gap_rate = round(score_rate - grade_average_rate, 4) if grade_average_rate is not None else None
        lost_score = round(max(full_score - score, 0.0), 4)
        priority_score = _calculate_priority_score(
            full_score=full_score,
            lost_score=lost_score,
            score_rate=score_rate,
            subject_weight=subject_weight_map.get((student_id, subject_id), 1.0),
        )
        diagnosis_label = _diagnose_knowledge(
            full_score=full_score,
            score_rate=score_rate,
            grade_gap_rate=grade_gap_rate,
        )
        question_numbers = sorted(data["questions"]) if isinstance(data.get("questions"), set) else []
        error_counter = data.get("error_tags")
        error_tags = _format_error_tag_stats(error_counter if isinstance(error_counter, Counter) else Counter())
        dominant_error_tag = error_tags[0]["tag"] if error_tags else None
        session.add(
            ScoreKnowledgeSnapshot(
                exam_id=exam_id,
                student_id=student_id,
                subject_id=subject_id,
                knowledge_point_id=knowledge_point_id,
                score=score,
                full_score=full_score,
                score_rate=score_rate,
                grade_average_rate=grade_average_rate,
                grade_gap_rate=grade_gap_rate,
                lost_score=lost_score,
                question_count=len(question_numbers),
                question_numbers_json=question_numbers,
                priority_score=priority_score,
                diagnosis_label=diagnosis_label,
                error_tags_json=error_tags,
                dominant_error_tag=dominant_error_tag,
                suggestion=_build_knowledge_suggestion(diagnosis_label, question_numbers, dominant_error_tag),
                rebuilt_at=now,
            )
        )
        created += 1
    session.flush()
    return created


def upsert_knowledge_point(session: Session, subject_id: int, name: str) -> KnowledgePoint:
    clean_name = name.strip()
    current = session.scalar(
        select(KnowledgePoint).where(
            KnowledgePoint.subject_id == subject_id,
            KnowledgePoint.name == clean_name,
        )
    )
    if current:
        current.is_active = True
        return current
    current = KnowledgePoint(subject_id=subject_id, name=clean_name)
    session.add(current)
    session.flush()
    return current


def upsert_question(
    session: Session,
    *,
    exam_id: int,
    subject_id: int,
    question_no: str,
    full_score: float,
    question_type: str | None,
    ability_level: str | None,
    sort_order: int,
) -> ScoreQuestion:
    clean_question_no = question_no.strip()
    question = session.scalar(
        select(ScoreQuestion).where(
            ScoreQuestion.exam_id == exam_id,
            ScoreQuestion.subject_id == subject_id,
            ScoreQuestion.question_no == clean_question_no,
        )
    )
    if question is None:
        question = ScoreQuestion(exam_id=exam_id, subject_id=subject_id, question_no=clean_question_no)
        session.add(question)
    question.full_score = full_score
    question.question_type = question_type
    question.ability_level = ability_level
    question.sort_order = sort_order
    question.is_active = True
    session.flush()
    return question


def replace_question_knowledge_points(
    session: Session,
    question_id: int,
    knowledge_points: list[int | KnowledgeResolveResult],
) -> None:
    normalized_items: list[tuple[int, str, str | None]] = []
    for item in knowledge_points:
        if isinstance(item, KnowledgeResolveResult):
            normalized_items.append((item.point.id, item.match_source, item.raw_text))
        else:
            normalized_items.append((item, "standard", None))
    unique_items = list({item[0]: item for item in normalized_items}.values())
    existing = {
        item.knowledge_point_id: item
        for item in session.scalars(
            select(ScoreQuestionKnowledgePoint).where(ScoreQuestionKnowledgePoint.question_id == question_id)
        ).all()
    }
    keep_ids = {item[0] for item in unique_items}
    for knowledge_point_id, match_source, raw_text in unique_items:
        item = existing.get(knowledge_point_id)
        if item is None:
            item = ScoreQuestionKnowledgePoint(
                question_id=question_id,
                knowledge_point_id=knowledge_point_id,
            )
            session.add(item)
        item.weight = 1.0
        item.match_source = match_source
        item.raw_knowledge_text = raw_text
        item.is_active = True
    for knowledge_point_id, item in existing.items():
        if knowledge_point_id not in keep_ids:
            item.is_active = False
    session.flush()


def _build_subject_weight_map(session: Session, exam_id: int) -> dict[tuple[int, int], float]:
    total_rank_map = {
        item.student_id: item.grade_rank
        for item in session.scalars(
            select(ScoreTotalSnapshot).where(
                ScoreTotalSnapshot.exam_id == exam_id,
                ScoreTotalSnapshot.is_active.is_(True),
            )
        ).all()
    }
    weights: dict[tuple[int, int], float] = {}
    for item in session.scalars(
        select(ScoreSubjectSnapshot).where(
            ScoreSubjectSnapshot.exam_id == exam_id,
            ScoreSubjectSnapshot.is_active.is_(True),
        )
    ).all():
        weight = 1.0
        total_rank = total_rank_map.get(item.student_id)
        rank_deviation = total_rank - item.grade_rank if total_rank is not None and item.grade_rank is not None else None
        if rank_deviation is not None:
            weight = 1.0 + min(max(abs(rank_deviation) / 100, 0.0), 0.5)
            if rank_deviation > 0:
                weight = 1.0
        elif item.grade_percentile is not None and item.grade_percentile < 0.35:
            weight = 1.2
        weights[(item.student_id, item.subject_id)] = weight
    return weights


def _calculate_priority_score(
    *,
    full_score: float,
    lost_score: float,
    score_rate: float,
    subject_weight: float,
) -> float:
    if full_score < MIN_KNOWLEDGE_FULL_SCORE:
        return 0.0
    improvement_space = max(1.0 - score_rate, 0.0)
    return round(lost_score * improvement_space * subject_weight, 4)


def _diagnose_knowledge(
    *,
    full_score: float,
    score_rate: float,
    grade_gap_rate: float | None,
) -> str:
    if full_score < MIN_KNOWLEDGE_FULL_SCORE:
        return "样本偏小"
    if score_rate < 0.55 and (grade_gap_rate is None or grade_gap_rate <= -0.05):
        return "优先补弱"
    if score_rate < 0.7:
        return "需要巩固"
    if grade_gap_rate is not None and grade_gap_rate <= -0.15:
        return "低于年级"
    return "正常"


def _extract_error_tag_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    names: list[str] = []
    for item in value:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
        elif isinstance(item, str):
            names.append(item)
    return [name for name in names if name]


def _format_error_tag_stats(counter: Counter[str]) -> list[dict[str, object]]:
    return [
        {"tag": tag, "count": count}
        for tag, count in counter.most_common()
        if tag and count > 0
    ]


def _build_knowledge_suggestion(label: str, question_numbers: list[str], dominant_error_tag: str | None = None) -> str:
    question_text = "、".join(question_numbers[:5]) or "相关题目"
    error_text = f"，重点排查“{dominant_error_tag}”" if dominant_error_tag else ""
    if label == "优先补弱":
        return f"先复盘 {question_text} 的基础概念和典型题型{error_text}，再安排同类基础题巩固。"
    if label == "需要巩固":
        return f"围绕 {question_text} 做错因整理{error_text}，并补 5-8 道同类题。"
    if label == "低于年级":
        return f"对照年级均值检查 {question_text} 的解题步骤{error_text}，优先补规范和易错点。"
    if label == "样本偏小":
        return "本知识点本次题量较少，仅作提醒，不单独作为学习重点。"
    return "保持常规复盘，后续结合多次考试再判断是否形成稳定短板。"
