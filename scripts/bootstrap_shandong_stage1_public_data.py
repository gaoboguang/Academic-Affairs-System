#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import xlrd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "app.db"
DEFAULT_SOURCE_DIR = ROOT / "data" / "gaokao_public_sources" / "shandong_stage1"
DEFAULT_BACKUP_DIR = ROOT / "data" / "backups"
SCRIPT_NAME = Path(__file__).name
USER_AGENT = "local-edu-tool-stage1-bootstrap/2026-04-24"


RANK_SOURCES = {
    2020: {
        "news_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=4938",
        "file_url": "https://www.sdzk.cn/Floadup/file/20200726/6373137724431062332329137.xls",
        "title": "2020年夏季高考文化总成绩一分一段表",
        "published_at": "2020-07-26",
    },
    2021: {
        "news_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5458",
        "file_url": "https://www.sdzk.cn/Floadup/file/20210625/6376023552787296505320142.xls",
        "title": "2021年夏季高考文化总成绩一分一段表",
        "published_at": "2021-06-25",
    },
    2022: {
        "news_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5794",
        "file_url": "https://www.sdzk.cn/Floadup/file/20220626/6379183893483079468961719.xls",
        "title": "2022年夏季高考文化成绩一分一段表",
        "published_at": "2022-06-26",
    },
    2023: {
        "news_url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212",
        "file_url": "https://www.sdzk.cn/Floadup/file/20230625/6382330466178390033845468.xls",
        "title": "2023年夏季高考文化成绩一分一段表",
        "published_at": "2023-06-25",
    },
}


SCORE_LINE_SOURCES = {
    2020: {
        "url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=4940",
        "title": "省教育厅、省教育招生考试院召开2020年高考工作第二次新闻发布会",
        "published_at": "2020-07-26",
    },
    2021: {
        "url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5462",
        "title": "省教育厅、省教育招生考试院召开2021年高考工作第二次新闻发布会",
        "published_at": "2021-06-25",
    },
    2022: {
        "url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5800",
        "title": "省教育厅召开2022年高考第二次新闻发布会",
        "published_at": "2022-06-25",
    },
    2023: {
        "url": "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6211",
        "title": "2023年普通高考第二次新闻发布会举行",
        "published_at": "2023-06-25",
    },
}


SCORE_LINES = {
    2020: [
        ("普通类", "常规批", "特殊类型招生控制线", 532, "夏季高考普通类特殊类型招生控制线"),
        ("普通类", "常规批", "一段线", 449, "夏季高考普通类一段线"),
        ("普通类", "常规批", "二段线", 150, "夏季高考普通类二段线"),
        ("普通类", "3+2对口贯通分段培养", "志愿填报资格线", 399, "3+2对口贯通分段培养高职志愿填报资格线"),
        ("艺术类", "文学编导/播音主持/摄影", "本科文化控制线", 381, "艺术类本科文化控制线"),
        ("艺术类", "美术/音乐/书法", "本科文化控制线", 314, "艺术类本科文化控制线"),
        ("艺术类", "舞蹈/戏剧影视表演/服装表演", "本科文化控制线", 291, "艺术类本科文化控制线"),
        ("艺术类", "专科", "专科文化控制线", 150, "艺术类专科文化控制线"),
        ("体育类", "常规批", "一段线", 561, "体育类一段线，综合分"),
        ("体育类", "常规批", "二段线", 457, "体育类二段线，综合分"),
        ("高水平运动员", "普通类一段线", "文化录取控制线", 449, "执行普通类一段线"),
        ("高水平运动员", "65%优惠", "文化录取控制线", 291, "执行普通类一段线65%"),
    ],
    2021: [
        ("普通类", "常规批", "特殊类型招生控制线", 518, "夏季高考普通类特殊类型招生控制线"),
        ("普通类", "常规批", "一段线", 444, "夏季高考普通类一段线"),
        ("普通类", "常规批", "二段线", 150, "夏季高考普通类二段线"),
        ("普通类", "3+2对口贯通分段培养", "志愿填报资格线", 394, "3+2对口贯通分段培养高职志愿填报资格线"),
        ("艺术类", "文学编导/播音主持/摄影", "本科文化控制线", 444, "艺术类本科文化控制线"),
        ("艺术类", "美术/音乐/书法/航空服务艺术", "本科文化控制线", 333, "艺术类本科文化控制线"),
        ("艺术类", "舞蹈/影视戏剧表演/服装表演", "本科文化控制线", 288, "艺术类本科文化控制线"),
        ("艺术类", "专科", "专科文化控制线", 150, "艺术类专科文化控制线"),
        ("体育类", "常规批", "一段线", 569, "体育类一段线，综合分"),
        ("体育类", "常规批", "二段线", 470, "体育类二段线，综合分"),
        ("高水平运动员", "普通类一段线", "文化录取控制线", 444, "执行普通类一段线"),
        ("高水平运动员", "65%优惠", "文化录取控制线", 288, "执行普通类一段线65%"),
        ("春季高考", "技能拔尖人才", "本科录取控制线", 150, "技能拔尖人才本科录取控制线"),
    ],
    2022: [
        ("普通类", "常规批", "特殊类型招生控制线", 513, "夏季高考普通类特殊类型招生控制线"),
        ("普通类", "常规批", "一段线", 437, "夏季高考普通类一段线"),
        ("普通类", "常规批", "二段线", 150, "夏季高考普通类二段线"),
        ("普通类", "3+2对口贯通分段培养", "志愿填报资格线", 387, "3+2对口贯通分段培养高职志愿填报资格线"),
        ("艺术类", "文学编导/播音主持/摄影", "本科文化控制线", 437, "艺术类本科文化控制线"),
        ("艺术类", "美术/音乐/书法/航空服务艺术", "本科文化控制线", 327, "艺术类本科文化控制线"),
        ("艺术类", "舞蹈/影视戏剧表演/服装表演", "本科文化控制线", 284, "艺术类本科文化控制线"),
        ("艺术类", "专科", "专科文化控制线", 150, "艺术类专科文化控制线"),
        ("体育类", "常规批", "一段线", 583, "体育类一段线，综合分"),
        ("体育类", "常规批", "二段线", 474, "体育类二段线，综合分"),
        ("高水平运动员", "普通类一段线", "文化录取控制线", 437, "执行普通类一段线"),
        ("高水平运动员", "65%优惠", "文化录取控制线", 284, "执行普通类一段线65%"),
        ("春季高考", "专科", "专科录取控制线", 150, "春季高考各专业类别专科录取控制线均为150分"),
    ],
    2023: [
        ("普通类", "常规批", "特殊类型招生控制线", 520, "夏季高考普通类特殊类型招生控制线"),
        ("普通类", "常规批", "一段线", 443, "夏季高考普通类一段线"),
        ("普通类", "常规批", "二段线", 150, "夏季高考普通类二段线"),
        ("普通类", "3+2对口贯通分段培养", "志愿填报资格线", 393, "3+2对口贯通分段培养高职志愿填报资格线"),
        ("艺术类", "文学编导/播音主持/摄影", "本科文化控制线", 443, "艺术类本科文化控制线"),
        ("艺术类", "美术/音乐/书法/航空服务艺术", "本科文化控制线", 332, "艺术类本科文化控制线"),
        ("艺术类", "舞蹈/戏剧影视表演/服装表演", "本科文化控制线", 287, "艺术类本科文化控制线"),
        ("艺术类", "专科", "专科文化控制线", 150, "艺术类专科文化控制线"),
        ("体育类", "常规批", "一段线", 587, "体育类一段线，综合分"),
        ("体育类", "常规批", "二段线", 480, "体育类二段线，综合分"),
        ("高水平运动员", "普通类一段线", "文化录取控制线", 443, "执行普通类一段线"),
        ("高水平运动员", "65%优惠", "文化录取控制线", 287, "执行普通类一段线65%"),
        ("春季高考", "技能拔尖人才", "本科录取控制线", 150, "技能拔尖人才本科录取控制线"),
        ("春季高考", "专科", "专科录取控制线", 150, "春季高考各专业类别专科录取控制线均为150分"),
        ("春季高考", "3+4对口贯通培养转段", "文化成绩合格标准", 160, "3+4对口贯通培养转段文化课总分合格标准"),
    ],
}


POLICY_REFERENCES = [
    (2020, "score_line", "2020年高考工作第二次新闻发布会：分数线与志愿政策", SCORE_LINE_SOURCES[2020]["url"], "公布2020年夏季高考普通类、艺术类、体育类分数线和志愿填报基本安排。"),
    (2021, "score_line", "2021年高考工作第二次新闻发布会：分数线与志愿政策", SCORE_LINE_SOURCES[2021]["url"], "公布2021年夏季高考各类别分数线、春季高考控制线和志愿填报提醒。"),
    (2022, "score_line", "2022年高考第二次新闻发布会：分数线与志愿政策", SCORE_LINE_SOURCES[2022]["url"], "公布2022年夏季高考普通类、艺术类、体育类分数线和录取工作提醒。"),
    (2023, "score_line", "2023年普通高考第二次新闻发布会：分数线与志愿政策", SCORE_LINE_SOURCES[2023]["url"], "公布2023年夏季高考普通类、艺术类、体育类分数线和春季高考控制线。"),
    (2020, "score_rank", "2020年夏季高考文化总成绩一分一段表", RANK_SOURCES[2020]["news_url"], "山东省教育招生考试院发布的夏季高考文化总成绩一分一段表。"),
    (2021, "score_rank", "2021年夏季高考文化总成绩一分一段表", RANK_SOURCES[2021]["news_url"], "山东省教育招生考试院发布的夏季高考文化总成绩一分一段表。"),
    (2022, "score_rank", "2022年夏季高考文化成绩一分一段表", RANK_SOURCES[2022]["news_url"], "山东省教育招生考试院发布的夏季高考文化成绩一分一段表。"),
    (2023, "score_rank", "2023年夏季高考文化成绩一分一段表", RANK_SOURCES[2023]["news_url"], "山东省教育招生考试院发布的夏季高考文化成绩一分一段表。"),
    (2023, "province_rule", "春季高考招生计划和专业类别划分", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6121", "说明2023年春季高考统一考试招生专业类别，共30个专业类别。"),
    (2023, "province_rule", "春季高考各批次志愿设置与填报规则", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6116", "说明春季高考本科提前批、本科批、专科批志愿设置与每次最多96个志愿等规则。"),
    (2022, "province_rule", "2022年山东省普通高等学校考试招生录取工作意见", "https://www.sdzk.cn/Floadup/file/20220419/6378599824430686785942103.pdf", "说明2022年普通类提前批、特殊类型批、常规批和艺术类、体育类批次及志愿数量规则。"),
    (2020, "province_rule", "2020年普通高校招生普通类和艺体春考志愿填报注意事项", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=4973", "说明2020年普通类、艺术类、体育类、春季高考志愿填报要求、选考科目要求和兼报限制。"),
    (2021, "province_rule", "2021年普通类提前批等第1次志愿填报注意事项", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5476", "说明2021年普通类提前批、体育类提前批、艺术类本科提前批及春季高考技能拔尖人才志愿填报注意事项。"),
    (2022, "province_rule", "2022年普通类提前批等第1次志愿填报注意事项", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=5816", "说明2022年普通类提前批、体育类提前批、艺术类本科提前批志愿填报范围、分数线和数量规则。"),
    (2023, "province_rule", "2023年普通类常规批本科计划等第1次志愿填报注意事项", "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6256", "说明2023年普通类特殊类型批、常规批本科计划、艺术类本科批、体育类常规批和春季高考本科批第1次志愿规则。"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Shandong stage 1 public gaokao data")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    db_path = args.db.resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")
    source_dir = args.source_dir.resolve()
    source_dir.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if not args.no_backup:
        backup_path = _backup_database(db_path, args.backup_dir.resolve())

    downloaded = _download_sources(source_dir)
    rank_rows = []
    for year, source in RANK_SOURCES.items():
        rank_rows.extend(_parse_rank_rows(downloaded[f"rank_{year}"], year, source))

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        before = _snapshot_counts(conn)
        rank_stats = _replace_score_rank_rows(conn, rank_rows)
        line_stats = _replace_score_line_rows(conn)
        policy_stats = _replace_policy_references(conn, source_dir)
        conn.commit()
        after = _snapshot_counts(conn)

    result = {
        "db_path": str(db_path),
        "backup_path": str(backup_path) if backup_path else None,
        "source_dir": str(source_dir),
        "downloaded": {key: str(path) for key, path in downloaded.items()},
        "rank_stats": rank_stats,
        "score_line_stats": line_stats,
        "policy_reference_stats": policy_stats,
        "before": before,
        "after": after,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"db: {db_path}")
        if backup_path:
            print(f"backup: {backup_path}")
        print(f"source_dir: {source_dir}")
        print(f"score_rank_segment inserted: {rank_stats['inserted']}, deleted: {rank_stats['deleted']}")
        print(f"gaokao_score_line inserted: {line_stats['inserted']}, deleted: {line_stats['deleted']}")
        print(f"gaokao_policy_reference inserted: {policy_stats['inserted']}, deleted: {policy_stats['deleted']}")
    return 0


def _download_sources(source_dir: Path) -> dict[str, Path]:
    downloaded: dict[str, Path] = {}
    for year, source in RANK_SOURCES.items():
        page_path = source_dir / f"sd_{year}_rank_page.html"
        file_path = source_dir / f"sd_{year}_rank.xls"
        _download(source["news_url"], page_path)
        _download(source["file_url"], file_path)
        downloaded[f"rank_page_{year}"] = page_path
        downloaded[f"rank_{year}"] = file_path
    for year, source in SCORE_LINE_SOURCES.items():
        page_path = source_dir / f"sd_{year}_score_line_page.html"
        _download(source["url"], page_path)
        downloaded[f"score_line_page_{year}"] = page_path
    for year, policy_type, title, url, _summary in POLICY_REFERENCES:
        filename = _safe_filename(f"policy_{year}_{policy_type}_{title}")
        suffix = ".pdf" if url.lower().endswith(".pdf") else ".html"
        path = source_dir / f"{filename}{suffix}"
        _download(url, path)
        downloaded[f"policy_{year}_{policy_type}_{_hash_text(url)[:8]}"] = path
    manifest = {
        "generated_at": _now_text(),
        "sources": {
            "rank_sources": RANK_SOURCES,
            "score_line_sources": SCORE_LINE_SOURCES,
            "policy_references": POLICY_REFERENCES,
        },
    }
    (source_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return downloaded


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        target.write_bytes(response.read())


def _parse_rank_rows(path: Path, year: int, source: dict[str, str]) -> list[dict[str, Any]]:
    if path.read_bytes()[:32].lower().startswith(b"<html"):
        rows = _read_html_excel_rows(path)
    else:
        rows = _read_xls_rows(path)
    header_index = next(index for index, row in enumerate(rows) if row and row[0] == "分数段")
    group_row = rows[header_index]
    subheader_row = rows[header_index + 1]
    group_starts = []
    current_group = None
    for index in range(1, max(len(group_row), len(subheader_row))):
        group_value = _cell_text(group_row[index] if index < len(group_row) else "")
        if group_value:
            current_group = _normalize_subject_group(group_value)
        subheader_value = _cell_text(subheader_row[index] if index < len(subheader_row) else "")
        next_subheader_value = _cell_text(subheader_row[index + 1] if index + 1 < len(subheader_row) else "")
        if current_group and subheader_value == "本段人数" and next_subheader_value == "累计人数":
            group_starts.append((index, current_group))

    parsed: list[dict[str, Any]] = []
    for row in rows[header_index + 2 :]:
        if not row:
            continue
        score = _to_int(row[0] if len(row) > 0 else None)
        if score is None:
            continue
        for column, subject_group in group_starts:
            segment_count = _to_int(row[column] if column < len(row) else None)
            cumulative_count = _to_int(row[column + 1] if column + 1 < len(row) else None)
            if segment_count is None and cumulative_count is None:
                continue
            parsed.append(
                {
                    "province": "山东",
                    "year": year,
                    "score_type": "summer_total",
                    "subject_group": subject_group,
                    "score": score,
                    "segment_count": segment_count,
                    "cumulative_count": cumulative_count,
                    "rank_value": cumulative_count,
                    "source_level": "official",
                    "source_title": source["title"],
                    "source_url": source["news_url"],
                    "local_source_path": str(path),
                    "parser_script_name": SCRIPT_NAME,
                    "published_at": source["published_at"],
                    "review_status": "confirmed_official_public",
                    "source_record_hash": _hash_text(f"rank|{year}|{subject_group}|{score}|{segment_count}|{cumulative_count}"),
                    "data_version_label": "shandong_stage1_public_20260424",
                    "import_batch_id": None,
                }
            )
    return parsed


def _read_xls_rows(path: Path) -> list[list[Any]]:
    sheet = xlrd.open_workbook(path).sheet_by_index(0)
    return [[_cell_text(value) for value in sheet.row_values(row_index)] for row_index in range(sheet.nrows)]


def _read_html_excel_rows(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I):
        cells = []
        for cell_html in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_html, re.S | re.I):
            cell_text = re.sub(r"<[^>]+>", "", cell_html)
            cells.append(_cell_text(html.unescape(cell_text)))
        rows.append(cells)
    return rows


def _replace_score_rank_rows(conn: sqlite3.Connection, rows: list[dict[str, Any]]) -> dict[str, int]:
    years = tuple(sorted({row["year"] for row in rows}))
    placeholders = ", ".join(["?"] * len(years))
    deleted = conn.execute(
        f'DELETE FROM score_rank_segment WHERE province = ? AND year IN ({placeholders})',
        ("山东", *years),
    ).rowcount
    columns = (
        "province",
        "year",
        "score_type",
        "subject_group",
        "score",
        "segment_count",
        "cumulative_count",
        "rank_value",
        "created_at",
        "updated_at",
        "source_level",
        "source_title",
        "source_url",
        "local_source_path",
        "parser_script_name",
        "published_at",
        "review_status",
        "source_record_hash",
        "data_version_label",
        "import_batch_id",
    )
    now = _now_text()
    payload = [tuple(row.get(column, now if column in {"created_at", "updated_at"} else None) for column in columns) for row in rows]
    conn.executemany(
        f'''
        INSERT INTO score_rank_segment ({", ".join(columns)})
        VALUES ({", ".join(["?"] * len(columns))})
        ''',
        payload,
    )
    return {"deleted": int(deleted or 0), "inserted": len(payload)}


def _replace_score_line_rows(conn: sqlite3.Connection) -> dict[str, int]:
    years = tuple(sorted(SCORE_LINES))
    placeholders = ", ".join(["?"] * len(years))
    deleted = conn.execute(
        f'DELETE FROM gaokao_score_line WHERE province = ? AND year IN ({placeholders})',
        ("山东", *years),
    ).rowcount
    now = _now_text()
    rows = []
    for year, items in SCORE_LINES.items():
        source = SCORE_LINE_SOURCES[year]
        for candidate_type, batch_name, line_type, score, remark in items:
            rows.append(
                (
                    "山东",
                    year,
                    candidate_type,
                    batch_name,
                    line_type,
                    score,
                    remark,
                    now,
                    now,
                    "official",
                    source["title"],
                    source["url"],
                    None,
                    SCRIPT_NAME,
                    source["published_at"],
                    "confirmed_official_public",
                    _hash_text(f"score_line|{year}|{candidate_type}|{batch_name}|{line_type}|{score}"),
                    "shandong_stage1_public_20260424",
                    None,
                )
            )
    conn.executemany(
        """
        INSERT INTO gaokao_score_line (
            province, year, candidate_type, batch_name, line_type, score, remark,
            created_at, updated_at, source_level, source_title, source_url,
            local_source_path, parser_script_name, published_at, review_status,
            source_record_hash, data_version_label, import_batch_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return {"deleted": int(deleted or 0), "inserted": len(rows)}


def _replace_policy_references(conn: sqlite3.Connection, source_dir: Path) -> dict[str, int]:
    urls = [item[3] for item in POLICY_REFERENCES]
    placeholders = ", ".join(["?"] * len(urls))
    deleted = conn.execute(
        f"DELETE FROM gaokao_policy_reference WHERE url IN ({placeholders})",
        tuple(urls),
    ).rowcount
    now = _now_text()
    rows = []
    for year, policy_type, title, url, summary in POLICY_REFERENCES:
        suffix = ".pdf" if url.lower().endswith(".pdf") else ".html"
        filename = _safe_filename(f"policy_{year}_{policy_type}_{title}") + suffix
        local_path = source_dir / filename
        rows.append(
            (
                "山东",
                year,
                policy_type,
                title,
                url,
                str(local_path) if local_path.exists() else None,
                summary,
                "official",
                None,
                None,
                f"{year}-01-01",
                now,
                now,
                "active",
            )
        )
    conn.executemany(
        """
        INSERT INTO gaokao_policy_reference (
            province, year, policy_type, title, url, local_path, summary,
            source_level, version_id, import_batch_id, published_at,
            created_at, updated_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return {"deleted": int(deleted or 0), "inserted": len(rows)}


def _snapshot_counts(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "score_rank_years": _year_counts(conn, "score_rank_segment"),
        "score_line_years": _year_counts(conn, "gaokao_score_line"),
        "policy_reference_total": conn.execute("SELECT COUNT(*) FROM gaokao_policy_reference").fetchone()[0],
    }


def _year_counts(conn: sqlite3.Connection, table: str) -> dict[str, int]:
    return {
        str(row["year"]): int(row["count"])
        for row in conn.execute(
            f'SELECT year, COUNT(*) AS count FROM "{table}" WHERE province = ? GROUP BY year ORDER BY year',
            ("山东",),
        ).fetchall()
    }


def _backup_database(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}_before_shandong_stage1_public_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


def _normalize_subject_group(value: str) -> str:
    mapping = {
        "选考政治": "选考思想政治",
        "思想政治": "选考思想政治",
        "政治": "选考思想政治",
    }
    return mapping.get(value, value)


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).replace("\xa0", "").strip()


def _to_int(value: Any) -> int | None:
    text = _cell_text(value)
    if not text:
        return None
    try:
        return int(float(text.replace(",", "")))
    except ValueError:
        return None


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", value).strip("_")
    return cleaned[:140] or "source"


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    sys.exit(main())
