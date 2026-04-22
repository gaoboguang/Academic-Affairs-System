from __future__ import annotations

from app.core.config import Settings


def ensure_runtime_directories(settings: Settings) -> None:
    for path in (
        settings.data_dir,
        settings.gaokao_data_dir,
        settings.uploads_dir,
        settings.backups_dir,
        settings.templates_dir,
        settings.exports_dir,
        settings.logs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
