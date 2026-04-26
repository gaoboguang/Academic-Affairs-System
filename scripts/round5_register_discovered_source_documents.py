#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.exc import OperationalError


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.core.config import Settings  # noqa: E402
from app.db.session import DatabaseManager  # noqa: E402
from app.services.gaokao_imports import (  # noqa: E402
    GaokaoSourceDocumentSeed,
    ensure_gaokao_import_directories,
    seed_gaokao_source_registry,
    upsert_gaokao_source_document,
)


@dataclass(frozen=True)
class DiscoveredSource:
    year: int
    source_type: str
    title: str
    url: str
    published_at: date
    note: str
    official_org: str = "山东省教育招生考试院"
    source_registry_code: str = "sdzk"
    parser_name: str | None = None
    province: str = "山东"


DISCOVERED_SOURCES: tuple[DiscoveredSource, ...] = (
    # 艺术 / 体育 / 春考投档情况表
    DiscoveredSource(2025, "art_filing_result", "山东省2025年艺术类本科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6986", date(2025, 7, 17), "第五轮发现；艺术类本科批投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2025, "art_filing_result", "山东省2025年艺术类专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=7009", date(2025, 7, 28), "第五轮发现；艺术类专科批投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2025, "sports_filing_result", "山东省2025年体育类常规批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6985", date(2025, 7, 17), "第五轮发现；体育类常规批投档来源，待解析综合分口径。"),
    DiscoveredSource(2025, "spring_exam_filing_result", "山东省2025年春季高考本科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6984", date(2025, 7, 17), "第五轮发现；春季高考本科批投档来源，待解析专业类别口径。"),
    DiscoveredSource(2025, "spring_exam_filing_result", "山东省2025年春季高考专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=7007", date(2025, 7, 28), "第五轮发现；春季高考专科批投档来源，待解析专业类别口径。"),
    DiscoveredSource(2024, "art_filing_result", "山东省2024年艺术类本科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6652", date(2024, 7, 17), "第五轮发现；艺术类本科批投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2024, "art_filing_result", "山东省2024年艺术类专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6672", date(2024, 7, 28), "第五轮发现；艺术类专科批投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2024, "sports_filing_result", "山东省2024年体育类常规批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6651", date(2024, 7, 17), "第五轮发现；体育类常规批投档来源，待解析综合分口径。"),
    DiscoveredSource(2024, "spring_exam_filing_result", "山东省2024年春季高考本科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6650", date(2024, 7, 17), "第五轮发现；春季高考本科批投档来源，待解析专业类别口径。"),
    DiscoveredSource(2024, "spring_exam_filing_result", "山东省2024年春季高考专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6669", date(2024, 7, 28), "第五轮发现；春季高考专科批投档来源，待解析专业类别口径。"),
    DiscoveredSource(2023, "art_filing_result", "山东省2023年艺术本科批统考第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6278", date(2023, 7, 17), "第五轮发现；艺术本科批统考投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2023, "art_filing_result", "山东省2023年艺术类专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6315", date(2023, 7, 28), "第五轮发现；艺术类专科批投档来源，待解析综合分/专业类别口径。"),
    DiscoveredSource(2023, "sports_filing_result", "山东省2023年体育类常规批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6276", date(2023, 7, 17), "第五轮发现；体育类常规批投档来源，待解析综合分口径。"),
    DiscoveredSource(2023, "spring_exam_filing_result", "山东省2023年春季高考本科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6277", date(2023, 7, 17), "第五轮发现；春季高考本科批投档来源，待解析专业类别口径。"),
    DiscoveredSource(2023, "spring_exam_filing_result", "山东省2023年春季高考专科批第1次志愿投档情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6312", date(2023, 7, 28), "第五轮发现；春季高考专科批投档来源，待解析专业类别口径。"),
    # 录取情况表 / 最低分
    DiscoveredSource(2025, "art_admission_min_score", "山东省2025年艺术类本科批第1次志愿录取情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989", date(2025, 7, 19), "第五轮发现；2025 艺术类本科录取情况表，优先考虑新增辅助表承载录取最低分/综合分。"),
    DiscoveredSource(2025, "sports_admission_min_score", "山东省2025年体育类常规批第1次志愿录取情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6987", date(2025, 7, 19), "第五轮发现；2025 体育类常规批录取情况表，优先考虑新增辅助表承载综合分。"),
    DiscoveredSource(2025, "spring_exam_admission_min_score", "山东省2025年春季高考本科批第1次志愿录取情况表", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6988", date(2025, 7, 19), "第五轮发现；2025 春季高考本科录取情况表，优先考虑新增辅助表承载专业类别口径。"),
    # 政策、百问百答和填报注意事项
    DiscoveredSource(2025, "admission_work_opinion", "山东省招生考试委员会办公室关于山东省2025年普通高等学校招生录取工作的意见", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6928", date(2025, 6, 18), "第五轮政策参考；录取批次、志愿填报和投档录取规则来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2024, "admission_work_opinion", "山东省招生考试委员会办公室关于山东省2024年普通高等学校招生录取工作的意见", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6547", date(2024, 6, 11), "第五轮政策参考；录取批次、志愿填报和投档录取规则来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2023, "admission_work_opinion", "关于山东省2023年普通高等学校招生录取工作的意见", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6205", date(2023, 6, 21), "第五轮政策参考；录取批次、志愿填报和投档录取规则来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2025, "policy_qa", "山东省普通高校招生志愿填报百问百答（2025版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6956", date(2025, 6, 27), "第五轮政策参考；志愿填报口径和用户解释来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2025, "policy_qa", "山东省普通高校招生考试政策百问百答（2025版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6871", date(2025, 5, 13), "第五轮政策参考；招生考试政策解释来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2024, "policy_qa", "山东省普通高校招生志愿填报百问百答（2024版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6591", date(2024, 6, 26), "第五轮政策参考；志愿填报口径和用户解释来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2024, "policy_qa", "山东省普通高校招生考试政策百问百答（2024版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6503", date(2024, 4, 23), "第五轮政策参考；招生考试政策解释来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2023, "policy_qa", "山东省普通高校招生志愿填报百问百答（2023版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6229", date(2023, 6, 27), "第五轮政策参考；志愿填报口径和用户解释来源。", parser_name="shandong_policy_reference"),
    DiscoveredSource(2023, "policy_qa", "山东省普通高校招生考试政策百问百答（2023版）", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6099", date(2023, 5, 24), "第五轮政策参考；招生考试政策解释来源。", parser_name="shandong_policy_reference"),
    # 招生计划补充信息
    DiscoveredSource(2025, "admission_plan_supplement", "山东省2025年普通高等学校分专业招生计划补充信息", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6955", date(2025, 6, 27), "第五轮计划来源；补充信息不是完整填报志愿指南，需作为部分补齐来源处理。"),
    DiscoveredSource(2025, "admission_plan_supplement", "山东省2025年普通高等学校专科层次分专业招生计划补充信息", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6990", date(2025, 7, 19), "第五轮计划来源；专科层次补充信息，不得当作完整招生计划。"),
    DiscoveredSource(2024, "admission_plan_supplement", "山东省2024年普通高等学校分专业招生计划补充信息", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6611", date(2024, 6, 27), "第五轮计划来源；补充信息不是完整填报志愿指南，需作为部分补齐来源处理。"),
    DiscoveredSource(2024, "admission_plan_supplement", "山东省2024年普通高等学校专科层次分专业招生计划补充信息", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6661", date(2024, 7, 22), "第五轮计划来源；专科层次补充信息，不得当作完整招生计划。"),
    DiscoveredSource(2023, "admission_plan_supplement", "山东省2023年普通高等学校分专业招生计划补充信息", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6222", date(2023, 6, 27), "第五轮计划来源；补充信息不是完整填报志愿指南，需作为部分补齐来源处理。"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register Round 5 discovered official Shandong source documents.")
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = _build_settings(args.db)
    manager = DatabaseManager(settings.database_url, settings.debug)
    try:
        with manager.session_scope() as session:
            payload = register_discovered_sources(session, settings)
    except OperationalError as exc:
        if "gaokao_source_document" in str(exc):
            print("高考来源登记表尚未创建，请先运行 `npm run backend:migrate`。", file=sys.stderr)
            return 2
        raise
    finally:
        manager.dispose()

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"第五轮发现来源已登记：新增 {payload['created']}，总计处理 {payload['total']}。")
    return 0


def register_discovered_sources(session, settings: Settings) -> dict[str, Any]:
    ensure_gaokao_import_directories(settings)
    seed_gaokao_source_registry(session)
    items: list[dict[str, Any]] = []
    created_count = 0
    for source in DISCOVERED_SOURCES:
        document, created = upsert_gaokao_source_document(
            session,
            GaokaoSourceDocumentSeed(
                province=source.province,
                year=source.year,
                source_type=source.source_type,
                title=source.title,
                url=source.url,
                official_org=source.official_org,
                source_registry_code=source.source_registry_code,
                published_at=source.published_at,
                parser_name=source.parser_name,
                note=source.note,
            ),
        )
        created_count += int(created)
        items.append(
            {
                "id": document.id,
                "created": created,
                "year": source.year,
                "source_type": source.source_type,
                "title": source.title,
                "url": source.url,
            }
        )
    return {"total": len(items), "created": created_count, "items": items}


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


if __name__ == "__main__":
    raise SystemExit(main())

