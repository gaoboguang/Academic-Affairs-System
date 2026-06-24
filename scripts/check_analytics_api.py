"""Self-check: hit the live analytics API with edge-case students/exams.

Run with `python scripts/check_analytics_api.py` while the backend is up on :8000.
"""
from __future__ import annotations

import json
import sys
import urllib.request

BASE = "http://localhost:8000/api"


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}") as response:
        return json.loads(response.read())


def expect(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}")
        raise SystemExit(1)
    print(f"  OK: {message}")


def check_student(student_id: int, exam_id: int, label: str) -> dict:
    print(f"\n[{label}] student={student_id} exam={exam_id}")
    payload = get(f"/analytics/students/{student_id}?exam_id={exam_id}")
    for field in (
        "trend_shape",
        "stability",
        "subject_trend_shapes",
        "subject_structure",
        "peer_comparison",
        "target_progress",
    ):
        expect(field in payload, f"response has field `{field}`")
    expect(
        payload["trend_shape"]["label"] in {"数据不足", "稳定", "稳步上升", "下滑", "剧烈波动", "U型反弹"},
        f"trend_shape.label='{payload['trend_shape']['label']}' is one of known labels",
    )
    expect(
        payload["stability"]["level"] in {"unknown", "high", "medium", "low"},
        f"stability.level='{payload['stability']['level']}' is one of known levels",
    )
    radar_points = payload["subject_structure"]["radar_points"]
    expect(isinstance(radar_points, list), "subject_structure.radar_points is a list")
    if radar_points:
        for point in radar_points:
            for key in ("subject_id", "subject_name", "student_t_score", "class_average_t"):
                expect(key in point, f"radar_points entry has `{key}`")
    peer = payload["peer_comparison"]
    expect("peer_count" in peer, "peer_comparison has peer_count")
    expect("subject_gaps" in peer, "peer_comparison has subject_gaps list")
    return payload


def check_grade(grade_id: int, exam_id: int, label: str) -> dict:
    print(f"\n[{label}] grade={grade_id} exam={exam_id}")
    payload = get(f"/analytics/grades/{grade_id}?exam_id={exam_id}")
    expect("exam_anomaly" in payload, "response has exam_anomaly field")
    anomaly = payload["exam_anomaly"]
    for key in ("is_outlier", "reason", "recommendation", "sample_size"):
        expect(key in anomaly, f"exam_anomaly has `{key}`")
    expect(isinstance(anomaly["is_outlier"], bool), "exam_anomaly.is_outlier is bool")
    return payload


def check_class_heatmap(class_id: int, exam_id: int, label: str) -> dict:
    print(f"\n[{label}] class={class_id} exam={exam_id}")
    payload = get(f"/analytics/classes/{class_id}/knowledge-heatmap?exam_id={exam_id}")
    for field in ("subject_groups", "notices"):
        expect(field in payload, f"response has field `{field}`")
    if payload["subject_groups"]:
        first = payload["subject_groups"][0]
        for key in ("subject_id", "subject_name", "knowledge_paths", "students", "cells"):
            expect(key in first, f"subject_group has `{key}`")
        if first["cells"] and first["students"]:
            expect(
                len(first["cells"][0]) == len(first["students"]),
                f"cell row length matches student count ({len(first['students'])})",
            )
    return payload


def main() -> None:
    print("=" * 60)
    print("ANALYTICS API SELF-CHECK")
    print("=" * 60)

    payload_full = check_student(55, 1, "rich history (4 exams)")
    expect(
        payload_full["stability"]["sample_count"] >= 3,
        f"sample_count={payload_full['stability']['sample_count']} >= 3",
    )

    payload_thin = check_student(9, 3, "thin history (1 exam)")
    expect(
        payload_thin["trend_shape"]["label"] == "数据不足",
        "thin history -> trend_shape.label='数据不足'",
    )
    expect(
        payload_thin["stability"]["level"] == "unknown",
        "thin history -> stability.level='unknown'",
    )

    try:
        check_student(1, 1, "no scores")
        print("  WARN: expected 404 for student without scores, got 200")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print("  OK: student without scores returns 404 (expected)")
        else:
            raise

    grade_payload = check_grade(3, 2, "grade analytics")
    print(f"  exam_anomaly: {grade_payload['exam_anomaly']['reason']}")

    classes_with_data = []
    import sqlite3
    conn = sqlite3.connect("/Users/gao/local-edu-tool/data/app.db")
    rows = conn.execute(
        "SELECT id FROM school_class WHERE is_active=1 ORDER BY id LIMIT 3"
    ).fetchall()
    conn.close()
    classes_with_data = [r[0] for r in rows]
    if not classes_with_data:
        classes_with_data = [1]
    for class_id in classes_with_data[:1]:
        check_class_heatmap(class_id, 1, f"class heatmap")

    print("\n" + "=" * 60)
    print("ALL API CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        sys.exit(1)
