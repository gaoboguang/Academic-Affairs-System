from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from app.core.bootstrap import ensure_runtime_directories
from app.core.config import Settings
from app.db.session import DatabaseManager
from app.main import create_app
from app.models import Base
from app.services.bootstrap import seed_demo_data, seed_reference_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本地教务工具桌面版后端入口")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18000)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--seed-demo", action="store_true")
    return parser


def bootstrap_database(settings: Settings, seed_demo: bool) -> None:
    ensure_runtime_directories(settings)
    db_manager = DatabaseManager(settings.database_url, settings.debug)
    Base.metadata.create_all(db_manager.engine)
    with db_manager.session_scope() as session:
        seed_reference_data(session)
        if seed_demo:
            seed_demo_data(session)
    db_manager.dispose()


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings(
        host=args.host,
        port=args.port,
        data_dir=args.data_dir,
        db_path=(args.data_dir / "app.db") if args.data_dir else None,
        allowed_origins=[
            "http://127.0.0.1:18080",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
    )
    bootstrap_database(settings, seed_demo=args.seed_demo)
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
