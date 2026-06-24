"""Dump backend OpenAPI schema to apps/frontend/openapi.json.

Run:
    python scripts/dump_openapi.py [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "apps" / "backend"
DEFAULT_OUTPUT = REPO_ROOT / "apps" / "frontend" / "openapi.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dump FastAPI OpenAPI schema to JSON.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination JSON path (default: apps/frontend/openapi.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    from app.main import create_app  # noqa: E402  imported lazily

    app = create_app()
    schema = app.openapi()

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    endpoint_count = sum(
        1
        for _, methods in schema.get("paths", {}).items()
        for _ in methods.values()
    )
    schema_count = len(schema.get("components", {}).get("schemas", {}))
    try:
        printable = output_path.relative_to(REPO_ROOT)
    except ValueError:
        printable = output_path
    print(
        f"wrote {printable}: "
        f"{endpoint_count} operations, {schema_count} schemas"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
