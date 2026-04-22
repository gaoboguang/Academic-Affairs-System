from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db_session(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.db
    with db.session_scope() as session:
        yield session


def get_gaokao_db_session(request: Request) -> Generator[Session | None, None, None]:
    db = getattr(request.app.state, "gaokao_db", None)
    if db is None:
        yield None
        return
    with db.session_scope() as session:
        yield session
