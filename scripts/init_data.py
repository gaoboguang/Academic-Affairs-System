from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "apps" / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.bootstrap import ensure_runtime_directories
from app.core.config import get_settings
from app.db.session import DatabaseManager
from app.services.bootstrap import seed_demo_data, seed_reference_data
from app.exporters.templates import generate_import_templates


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化本地教务工具基础数据。")
    parser.add_argument("--demo", action="store_true", help="同时写入示例演示数据")
    args = parser.parse_args()

    settings = get_settings()
    ensure_runtime_directories(settings)
    generate_import_templates(settings)

    db_manager = DatabaseManager(settings.database_url, settings.debug)
    with db_manager.session_scope() as session:
        seed_reference_data(session)
        if args.demo:
            seed_demo_data(session)

    print("初始化完成。")


if __name__ == "__main__":
    main()

