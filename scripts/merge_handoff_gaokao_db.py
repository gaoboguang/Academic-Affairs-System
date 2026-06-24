#!/usr/bin/env python3
"""Deprecated: raw gaokao tables now live in the sidecar database.

The original workflow merged the Windows/Mac handoff database into
``data/app.db``. After the B-plan migration (2026-05) the 22 raw tables are
kept in ``data/local_edu_tool/local_edu.sqlite3`` and are ATTACHed at runtime.
Running this script is no longer needed for day-to-day development; it is
retained only to make the deprecation discoverable.
"""
from __future__ import annotations

import sys


def main() -> int:
    message = (
        "[deprecated] scripts/merge_handoff_gaokao_db.py 已不再使用。\n"
        "raw 表现在直接位于 data/local_edu_tool/local_edu.sqlite3，\n"
        "应用启动时通过 ATTACH 自动接入。"
    )
    print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
